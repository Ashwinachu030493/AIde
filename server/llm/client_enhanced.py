import litellm
from litellm import completion, acompletion
from typing import Dict, Optional, AsyncGenerator, List, Any, Union
import os
import json
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class UserLLMConfig:
    """User's LLM configuration loaded from settings"""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None
    default_model: str = "gpt-4-turbo-preview"
    preferred_providers: List[str] = field(default_factory=lambda: ['openai', 'anthropic', 'groq', 'huggingface'])
    
    def __post_init__(self):
        if self.preferred_providers is None:
            self.preferred_providers = ['openai', 'anthropic', 'groq', 'huggingface']

class EnhancedLLMClient:
    """LLM client that uses user-specific API keys"""
    
    def __init__(self, user_config: UserLLMConfig = None):
        self.user_config = user_config or UserLLMConfig()
        self.cache = {}  # Simple in-memory cache for now
        self.usage_stats = {
            'total_tokens': 0,
            'total_cost': 0.0,
            'requests_by_provider': {}
        }
        
        # Set verbose logging for dev
        litellm.set_verbose = os.getenv("APP_ENV") == "development"
    
    def update_config(self, user_config: UserLLMConfig):
        """Update user configuration (call when settings change)"""
        self.user_config = user_config
        logger.info(f"LLM client updated with user config. Model: {user_config.default_model}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of providers user has configured"""
        providers = []
        
        if self.user_config.openai_api_key:
            providers.append('openai')
        if self.user_config.anthropic_api_key:
            providers.append('anthropic')
        if self.user_config.groq_api_key:
            providers.append('groq')
        if self.user_config.huggingface_api_key:
            providers.append('huggingface')
        
        # Fallback to environment variables if no user keys
        if not providers:
            if os.getenv('OPENAI_API_KEY'):
                providers.append('openai')
            if os.getenv('ANTHROPIC_API_KEY'):
                providers.append('anthropic')
            if os.getenv('GROQ_API_KEY'):
                providers.append('groq')
            if os.getenv('HUGGINGFACE_API_KEY'):
                providers.append('huggingface')
        
        return providers
    
    def _get_model_provider(self, model: str) -> str:
        """Determine which provider a model belongs to"""
        if model.lower().startswith('gpt-'):
            return 'openai'
        elif model.lower().startswith('claude-'):
            return 'anthropic'
        elif 'llama' in model.lower() or 'mixtral' in model.lower():
            if model.startswith('huggingface/'):
                return 'huggingface'
            return 'groq'
        elif model.startswith('huggingface/'):
            return 'huggingface'
        else:
            return 'openai'  # Default fallback
    
    def _get_api_key_for_provider(self, provider: str) -> Optional[str]:
        """Get API key for a provider from user config or env"""
        key_map = {
            'openai': self.user_config.openai_api_key,
            'anthropic': self.user_config.anthropic_api_key,
            'groq': self.user_config.groq_api_key,
            'huggingface': self.user_config.huggingface_api_key
        }
        
        # Try user config first
        user_key = key_map.get(provider)
        if user_key:
            return user_key
        
        # Fallback to environment
        env_map = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'groq': 'GROQ_API_KEY',
            'huggingface': 'HUGGINGFACE_API_KEY'
        }
        
        env_var = env_map.get(provider)
        if env_var:
            return os.getenv(env_var)
            
        return None
    
    async def get_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        streaming: bool = False,
        **kwargs
    ) -> Union[AsyncGenerator[str, None], str]:
        """Get LLM completion using user's API keys"""
        
        # Determine model to use
        if model is None:
            model = self.user_config.default_model
        
        # Determine provider
        provider = self._get_model_provider(model)
        
        # Get API key
        api_key = self._get_api_key_for_provider(provider)
        if not api_key:
            available = self.get_available_providers()
            error_msg = f"No API key found for {provider} (model: {model}). Available: {available}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Prepare litellm parameters
        litellm_params = {
            "model": model,
            "messages": messages,
            "stream": streaming,
            "api_key": api_key,
            **kwargs
        }
        
        # Add provider-specific parameters
        if provider == 'anthropic':
            litellm_params['max_tokens'] = litellm_params.get('max_tokens', 4000)
        
        try:
            timestamp = datetime.now()
            
            if streaming:
                # Stream response
                response = await acompletion(**litellm_params)
                
                async def stream_generator():
                    full_response = ""
                    async for chunk in response:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            yield content
                    
                    # Update stats after stream complete
                    self._update_stats(provider, full_response)
                
                return stream_generator()
                
            else:
                # Get full response
                response = await acompletion(**litellm_params)
                
                content = response.choices[0].message.content
                
                # Update stats
                self._update_stats(provider, content)
                
                return content
                
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            
            # Try fallback providers if this wasn't a budget model request
            # Simple fallback to GPT-3.5-Turbo if strictly necessary, 
            # but usually we want to respect the user's choice or fail clearly first.
            # For now, let's re-raise to show the error in UI.
            raise
    
    def _update_stats(self, provider: str, content: str):
        """Update usage statistics"""
        # Rough token estimation
        token_count = len(content) // 4
        
        self.usage_stats['total_tokens'] += token_count
        
        # Update provider counts
        requests_map = self.usage_stats.get('requests_by_provider', {})
        requests_map[provider] = requests_map.get(provider, 0) + 1
        self.usage_stats['requests_by_provider'] = requests_map
        
        # Log for debugging
        logger.debug(f"Used ~{token_count} tokens via {provider}")
    
    def get_stats(self) -> Dict:
        """Get usage statistics"""
        return self.usage_stats
