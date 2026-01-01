"""
shared//schemas.py

共享的 Pydantic 模型。

此模块定义了前后端共享的数据模型，包括 API 请求和响应模型。
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class GreetingResponse(BaseModel):
    message: str

# --- LLM Config Schemas ---
class LLMConfigCreate(BaseModel):
    provider: str
    model_name: str
    api_key_name: str
    base_url: Optional[str] = None


class LLMConfigRead(BaseModel):
    id: int
    provider: str
    model_name: str
    api_key_name: str
    base_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # 兼容从 ORM 对象转换


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