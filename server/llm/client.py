import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional, Union

import litellm
from litellm import acompletion
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class UserLLMConfig:
    """User's LLM configuration loaded from settings."""

    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None
    default_model: str = "gpt-4-turbo-preview"
    preferred_providers: List[str] = field(
        default_factory=lambda: ["openai", "anthropic", "groq", "huggingface"]
    )

    def __post_init__(self):
        if self.preferred_providers is None:
            self.preferred_providers = ["openai", "anthropic", "groq", "huggingface"]


class LLMClient:
    """Unified LLM client with routing, user-config keys, and optional DB logging."""

    MODEL_ROUTING: Dict[str, Dict[str, str]] = {
        "brainstorming": {
            "primary": "claude-3-5-sonnet-20241022",
            "fallback": "gpt-4-turbo-preview",
            "budget_model": "gpt-3.5-turbo",
        },
        "code_generation": {
            "primary": "gpt-4-turbo-preview",
            "fallback": "claude-3-5-sonnet-20241022",
            "budget_model": "gpt-3.5-turbo",
        },
        "debugging": {
            "primary": "gpt-4-turbo-preview",
            "fallback": "claude-3-5-sonnet-20241022",
            "budget_model": "claude-3-haiku-20240307",
        },
        "code_explanation": {
            "primary": "claude-3-haiku-20240307",
            "fallback": "gpt-3.5-turbo",
            "budget_model": "gpt-3.5-turbo",
        },
    }

    def __init__(
        self, user_config: Optional[UserLLMConfig] = None, db_session: Optional[Session] = None
    ):
        self.user_config = user_config or UserLLMConfig()
        self.db = db_session
        self.usage_stats: Dict[str, Union[int, float, Dict[str, int]]] = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "requests_by_provider": {},
        }
        litellm.set_verbose = os.getenv("APP_ENV") == "development"

    # Provider and key helpers -------------------------------------------------
    def get_available_providers(self) -> List[str]:
        providers: List[str] = []
        if self.user_config.openai_api_key:
            providers.append("openai")
        if self.user_config.anthropic_api_key:
            providers.append("anthropic")
        if self.user_config.groq_api_key:
            providers.append("groq")
        if self.user_config.huggingface_api_key:
            providers.append("huggingface")

        if not providers:
            if os.getenv("OPENAI_API_KEY"):
                providers.append("openai")
            if os.getenv("ANTHROPIC_API_KEY"):
                providers.append("anthropic")
            if os.getenv("GROQ_API_KEY"):
                providers.append("groq")
            if os.getenv("HUGGINGFACE_API_KEY"):
                providers.append("huggingface")
        return providers

    def _get_model_provider(self, model: str) -> str:
        mlower = model.lower()
        if mlower.startswith("gpt-"):
            return "openai"
        if mlower.startswith("claude-"):
            return "anthropic"
        if "llama" in mlower or "mixtral" in mlower:
            if model.startswith("huggingface/"):
                return "huggingface"
            return "groq"
        if model.startswith("huggingface/"):
            return "huggingface"
        return "openai"

    def _get_api_key_for_provider(self, provider: str) -> Optional[str]:
        key_map = {
            "openai": self.user_config.openai_api_key,
            "anthropic": self.user_config.anthropic_api_key,
            "groq": self.user_config.groq_api_key,
            "huggingface": self.user_config.huggingface_api_key,
        }
        user_key = key_map.get(provider)
        if user_key:
            return user_key
        env_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "groq": "GROQ_API_KEY",
            "huggingface": "HUGGINGFACE_API_KEY",
        }
        env_var = env_map.get(provider)
        return os.getenv(env_var) if env_var else None

    # Core completion ----------------------------------------------------------
    async def get_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        streaming: bool = False,
        task_type: str = "code_explanation",
        user_tier: str = "free",
        project_id: Optional[str] = None,
        operation: str = "chat",
        **kwargs,
    ) -> Union[AsyncGenerator[str, None], str]:
        model_name, fallback_model = self._resolve_model(model, task_type, user_tier)
        provider = self._get_model_provider(model_name)
        api_key = self._get_api_key_for_provider(provider)
        if not api_key:
            available = self.get_available_providers()
            msg = f"No API key for provider {provider}. Available: {available}"
            logger.error(msg)
            raise ValueError(msg)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        params = {
            "model": model_name,
            "messages": messages,
            "stream": streaming,
            "api_key": api_key,
            **kwargs,
        }
        if provider == "anthropic":
            params["max_tokens"] = params.get("max_tokens", 4000)

        prompt_tokens = self._estimate_tokens(prompt, system_prompt)

        try:
            if streaming:
                response = await acompletion(**params)

                async def stream_gen():
                    full_response = ""
                    async for chunk in response:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            yield content
                    await self._log_usage(
                        provider, model_name, operation, prompt_tokens, full_response, project_id
                    )
                    self._update_stats(provider, full_response)

                return stream_gen()

            response = await acompletion(**params)
            content = response.choices[0].message.content
            await self._log_usage(
                provider, model_name, operation, prompt_tokens, content, project_id
            )
            self._update_stats(provider, content)
            return content

        except Exception as e:
            logger.error(f"LLM request failed for {model_name}: {e}")
            if fallback_model and model_name != fallback_model:
                try:
                    params["model"] = fallback_model
                    params["stream"] = streaming
                    if streaming:
                        response = await acompletion(**params)

                        async def fb_stream_gen():
                            full_response = ""
                            async for chunk in response:
                                if chunk.choices and chunk.choices[0].delta.content:
                                    content = chunk.choices[0].delta.content
                                    full_response += content
                                    yield content
                            await self._log_usage(
                                provider,
                                fallback_model,
                                f"{operation}_fallback",
                                prompt_tokens,
                                full_response,
                                project_id,
                            )
                            self._update_stats(provider, full_response)

                        return fb_stream_gen()
                    else:
                        response = await acompletion(**params)
                        content = response.choices[0].message.content
                        await self._log_usage(
                            provider,
                            fallback_model,
                            f"{operation}_fallback",
                            prompt_tokens,
                            content,
                            project_id,
                        )
                        self._update_stats(provider, content)
                        return content
                except Exception as fb_err:
                    logger.error(f"Fallback model {fallback_model} also failed: {fb_err}")
            # Log failure
            await self._log_usage(
                provider,
                model_name,
                f"{operation}_failed",
                prompt_tokens,
                "",
                project_id,
                error=str(e),
            )
            raise

    # Helpers -----------------------------------------------------------------
    def _resolve_model(
        self, model: Optional[str], task_type: str, user_tier: str
    ) -> tuple[str, Optional[str]]:
        if model:
            return model, None
        routing = self.MODEL_ROUTING.get(task_type, self.MODEL_ROUTING["code_explanation"])
        if user_tier == "free":
            return routing["budget_model"], routing.get("fallback")
        return routing["primary"], routing.get("fallback")

    def _estimate_tokens(self, prompt: str, system_prompt: Optional[str]) -> int:
        tokens = len(prompt) // 4
        if system_prompt:
            tokens += len(system_prompt) // 4
        return tokens

    def _update_stats(self, provider: str, content: str):
        token_count = len(content) // 4
        self.usage_stats["total_tokens"] += token_count
        requests_map = self.usage_stats.get("requests_by_provider", {})
        requests_map[provider] = requests_map.get(provider, 0) + 1
        self.usage_stats["requests_by_provider"] = requests_map

    async def _log_usage(
        self,
        provider: str,
        model: str,
        operation: str,
        prompt_tokens: int,
        completion_text: str,
        project_id: Optional[str],
        error: Optional[str] = None,
    ):
        if not self.db:
            return
        try:
            from server.models.llm_usage import LLMUsageLog

            completion_tokens = len(completion_text) // 4
            total_tokens = prompt_tokens + completion_tokens
            cost_per_1k = {
                "gpt-4-turbo-preview": 0.01,
                "gpt-4": 0.03,
                "gpt-3.5-turbo": 0.001,
                "claude-3-opus": 0.015,
                "claude-3-sonnet": 0.003,
                "claude-3-haiku": 0.00025,
                "llama3-70b-8192": 0.00079,
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
                error_message=error,
            )
            self.db.add(usage_log)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log usage: {e}")
