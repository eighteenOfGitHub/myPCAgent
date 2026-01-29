# shared/chat_schemas.py

from datetime import datetime
from pydantic import BaseModel

# --- Chat Session Schemas ---
class ChatSessionCreate(BaseModel):
    title: str = "新对话"
    config_id: int

class ChatSessionRead(BaseModel):
    id: int
    title: str
    config_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Chat Message Schemas ---
class ChatMessageCreate(BaseModel):
    role: str
    content: str

class ChatMessageRead(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Chat Turn (High-level Interaction) ---
class ChatTurnRequest(BaseModel):
    session_id: int
    user_message: str | None = None

class ChatTurnResponse(BaseModel):
    session_id: int
    user_message: str
    assistant_reply: str
    message_id: int
