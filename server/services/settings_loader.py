import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from server.llm.client import UserLLMConfig
from server.models.user_simple import UserSettings
from server.services.encryption_simple import SimpleEncryption

logger = logging.getLogger(__name__)


class SettingsLoader:
    """Load and decrypt user settings from database"""

    def __init__(self):
        self.encryption = SimpleEncryption()

    def load_user_settings(self, db: Session) -> Optional[Dict[str, Any]]:
        """Load user settings from database"""

        settings = db.query(UserSettings).filter_by(is_active=1).first()
        if not settings:
            return None

        # Decrypt API keys
        decrypted_keys = {}
        for provider in ["openai", "anthropic", "groq", "github"]:
            field_name = f"{provider}_api_key"
            encrypted = getattr(settings, field_name, None)
            if encrypted:
                decrypted = self.encryption.decrypt(encrypted)
                if decrypted:
                    decrypted_keys[provider] = decrypted

        return {
            "id": settings.id,
            "openai_api_key": decrypted_keys.get("openai"),
            "anthropic_api_key": decrypted_keys.get("anthropic"),
            "groq_api_key": decrypted_keys.get("groq"),
            "github_api_key": decrypted_keys.get("github"),
            "default_model": settings.default_model,
            "theme": settings.theme,
            "auto_ingest": bool(settings.auto_ingest),
            "max_file_size_mb": settings.max_file_size_mb,
            "telemetry_opted_in": bool(settings.telemetry_opted_in),
            "error_reporting_opted_in": bool(settings.error_reporting_opted_in),
            "created_at": settings.created_at,
            "updated_at": settings.updated_at,
        }

    def load_llm_config(self, db: Session) -> UserLLMConfig:
        """Load LLM-specific configuration"""
        settings = self.load_user_settings(db)

        if not settings:
            # Return empty config (will use env vars as fallback)
            return UserLLMConfig()

        return UserLLMConfig(
            openai_api_key=settings.get("openai_api_key"),
            anthropic_api_key=settings.get("anthropic_api_key"),
            groq_api_key=settings.get("groq_api_key"),
            default_model=settings.get("default_model", "gpt-4-turbo-preview"),
            preferred_providers=self._get_preferred_providers(settings),
        )

    def _get_preferred_providers(self, settings: Dict[str, Any]) -> List[str]:
        """Determine preferred providers based on available keys"""
        providers = []

        if settings.get("openai_api_key"):
            providers.append("openai")
        if settings.get("anthropic_api_key"):
            providers.append("anthropic")
        if settings.get("groq_api_key"):
            providers.append("groq")

        return providers if providers else ["openai", "anthropic", "groq"]
