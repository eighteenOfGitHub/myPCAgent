"""shared/schemas.py共享的 Pydantic 模型。此模块定义了前后端共享的数据模型，包括 API 请求和响应模型。"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum  # 新增：用于 LLMProvider 枚举


# --- 新增：LLM Provider 枚举 ---
class LLMProvider(str, Enum):  # 新增
    OPENAI = "OpenAI"
    OLLAMA = "Ollama"
    # 未来可扩展其他 provider


class GreetingResponse(BaseModel):
    message: str

# --- LLM Config Schemas ---
class LLMConfigCreate(BaseModel):
    provider: LLMProvider
    model_name: str
    api_key: str  # 改为 api_key
    base_url: Optional[str] = None

# --- 新增：LLM 配置响应模型（不含敏感信息）---
class LLMConfigResponse(BaseModel):  # 新增
    id: int
    provider: LLMProvider
    model_name: str
    base_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- 新增：LLM 测试响应模型 ---
class LLMTestResponse(BaseModel):  # 新增
    success: bool
    message: Optional[str] = None

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