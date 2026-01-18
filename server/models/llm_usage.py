from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from server.shared.database import Base


class LLMUsageLog(Base):
    __tablename__ = "llm_usage_logs"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    operation = Column(String(50), nullable=False)

    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)

    user_id = Column(String(100), default="local_user")
    project_id = Column(String(100))
    error_message = Column(Text)

    timestamp = Column(DateTime(timezone=True), server_default=func.now())
