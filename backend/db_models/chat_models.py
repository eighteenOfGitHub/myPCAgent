# backend/db_models/chat_models.py

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime

from backend.db_models.user_config import LLMConfig

class ChatSession(SQLModel, table=True):
    """聊天会话主表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(default="新对话", max_length=100)
    config_id: int = Field(foreign_key="llmconfig.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    config: "LLMConfig" = Relationship(back_populates="sessions")
    messages: list["ChatMessage"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"order_by": "ChatMessage.created_at"}
    )


class ChatMessage(SQLModel, table=True):
    """聊天消息明细表（含 LLM 模型快照，确保历史可追溯）"""
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chat_session.id", index=True)
    role: str = Field(description="'user' 或 'assistant'")
    content: str = Field(description="消息内容")
    llm_provider: str = Field(description="消息生成时使用的 LLM 提供商（如 openai、ollama）")
    llm_model_name: str = Field(description="消息生成时使用的具体模型名称")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    session: "ChatSession" = Relationship(back_populates="messages")