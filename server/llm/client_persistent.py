import litellm
from litellm import acompletion
from typing import Dict, Optional, AsyncGenerator, List, Union
import json
import asyncio
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from server.llm.client_enhanced import EnhancedLLMClient, UserLLMConfig

logger = logging.getLogger(__name__)

class PersistentLLMClient(EnhancedLLMClient):
    """LLM client that persists usage data to database"""
    
    def __init__(self, user_config: UserLLMConfig = None, db_session: Session = None):
        super().__init__(user_config)
        self.db = db_session
        
    async def get_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        streaming: bool = False,
        project_id: Optional[str] = None,
        operation: str = "chat",
        **kwargs
    ) -> Union[AsyncGenerator[str, None], str]:
        """Get completion and log usage to database"""
        
        # Determine model
        if model is None:
            model = self.user_config.default_model
            
        provider = self._get_model_provider(model)
        
        # Track start time and token counts
        prompt_tokens = len(prompt) // 4  # Rough estimate
        if system_prompt:
            prompt_tokens += len(system_prompt) // 4
            
        try:
            if streaming:
                # Delegate to parent for logic, but we need to intercept the stream
                # Re-implementing specific parts to wrap stream
                
                # Get API key (logic from parent)
                api_key = self._get_api_key_for_provider(provider)
                if not api_key:
                    raise ValueError(f"No API key for {provider}")

                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                litellm_params = {
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "api_key": api_key,
                    **kwargs
                }
                
                if provider == 'anthropic':
                    litellm_params['max_tokens'] = litellm_params.get('max_tokens', 4000)

                response = await acompletion(**litellm_params)
                
                async def stream_wrapper():
                    full_response = ""
                    async for chunk in response:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            yield content
                    
                    # Log usage after stream
                    completion_tokens = len(full_response) // 4
                    total_tokens = prompt_tokens + completion_tokens
                    
                    await self._log_usage(
                        provider=provider,
                        model=model,
                        operation=operation,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        project_id=project_id
                    )
                    
                    self._update_stats(provider, full_response)

                return stream_wrapper()
                
            else:
                # Non-streaming
                # Call parent method directly? 
                # Parent _update_stats only does in-memory.
                # It's cleaner to just call litellm here to control logging.
                
                api_key = self._get_api_key_for_provider(provider)
                if not api_key:
                     raise ValueError(f"No API key for {provider}")

                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                litellm_params = {
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "api_key": api_key,
                    **kwargs
                }
                
                if provider == 'anthropic':
                     litellm_params['max_tokens'] = litellm_params.get('max_tokens', 4000)

                response = await acompletion(**litellm_params)
                content = response.choices[0].message.content
                
                completion_tokens = len(content) // 4
                total_tokens = prompt_tokens + completion_tokens
                
                await self._log_usage(
                    provider=provider,
                    model=model,
                    operation=operation,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    project_id=project_id
                )
                
                self._update_stats(provider, content)
                return content
                
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            # Try log error
            await self._log_usage(
                provider=provider,
                model=model,
                operation=f"{operation}_failed",
                prompt_tokens=prompt_tokens,
                completion_tokens=0,
                total_tokens=prompt_tokens,
                project_id=project_id,
                error=str(e)
            )
            raise
    
    async def _log_usage(
        self,
        provider: str,
        model: str,
        operation: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        project_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Log usage to database"""
        if not self.db:
            return
        
        try:
            from server.models.llm_usage import LLMUsageLog
            
            # Simple cost estimation
            cost_per_1k = {
                'gpt-4-turbo-preview': 0.01,
                'gpt-4': 0.03,
                'gpt-3.5-turbo': 0.001,
                'claude-3-opus': 0.015,
                'claude-3-sonnet': 0.003,
                'claude-3-haiku': 0.00025,
                'llama3-70b-8192': 0.00079,
            }
            
            base_cost = cost_per_1k.get(model, 0.001)
            estimated_cost = (total_tokens / 1000) * base_cost
            
            usage_log = LLMUsageLog(
                provider=provider,
                model=model,
                operation=operation,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=estimated_cost,
                project_id=project_id,
                error_message=error
            )
            
            self.db.add(usage_log)
            # Commit is tricky in async context if db session is shared/managed by dependency
            # Ideally we should use a separate session or ensuring it's safe.
            # Assuming 'db' is a standard session.
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log usage: {e}")
