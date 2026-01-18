from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from server.shared.database import Base


class UserSettings(Base):
    """Simple user settings for single-user local app"""

    __tablename__ = "user_settings"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    is_active = Column(Integer, default=1)  # SQLite pseudo-boolean

    # API Keys (encrypted, base64 encoded)
    openai_api_key = Column(Text)
    anthropic_api_key = Column(Text)
    groq_api_key = Column(Text)
    github_api_key = Column(Text)  # Was github_token, renamed for consistency
    huggingface_api_key = Column(Text)

    # Preferences
    default_model = Column(String(50), default="gpt-4-turbo-preview")
    theme = Column(String(20), default="system")
    auto_ingest = Column(Integer, default=1)
    max_file_size_mb = Column(Integer, default=10)

    # Privacy
    telemetry_opted_in = Column(Integer, default=0)
    error_reporting_opted_in = Column(Integer, default=0)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class APIKeyUsage(Base):
    """Log API key usage for auditing"""

    __tablename__ = "api_key_usage"

    id = Column(Integer, primary_key=True)
    provider = Column(String(50), nullable=False)
    operation = Column(String(100), nullable=False)
    success = Column(Integer, default=1)
    error_message = Column(Text)
    timestamp = Column(DateTime, default=func.now())
