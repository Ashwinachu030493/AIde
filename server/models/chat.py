from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class MessageCreate(BaseModel):
    content: str
    role: str = "user"


class ChatMessage(BaseModel):
    type: str = "message"
    content: str
    context: Optional[Dict[str, Any]] = {}


class ConversationCreate(BaseModel):
    project_id: Optional[str] = None
    title: Optional[str] = None
