from pydantic import BaseModel
from typing import Optional, Dict, Any, List

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
