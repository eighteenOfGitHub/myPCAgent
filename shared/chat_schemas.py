# shared/chat_schemas.py

from datetime import datetime
from pydantic import BaseModel
from typing import Optional

# --- Chat Session Schemas ---
class ChatSessionCreate(BaseModel):
    # 用户首条消息，用于生成会话标题
    first_message: str
    # 可选：允许前端占位，后端将使用默认 LLM 生成标题
    title: Optional[str] = None
    # 可选：未提供时由后端选择默认配置
    config_id: Optional[int] = None

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
    config_id: Optional[int] = None

class ChatTurnResponse(BaseModel):
    session_id: int
    assistant_reply: str
    message_id: int
