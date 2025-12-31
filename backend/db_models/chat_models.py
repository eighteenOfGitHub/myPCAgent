# backend/db_models/chat_models.py

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship


class LLMConfig(SQLModel, table=True):
    """大语言模型配置表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str = Field(index=True, description="LLM 服务提供商")
    model_name: str = Field(description="具体模型名称")
    api_key_name: str = Field(description="环境变量中存储 API Key 的名称")
    base_url: Optional[str] = Field(default=None, description="自定义 API 基础 URL")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    sessions: list["ChatSession"] = Relationship(back_populates="config")


class ChatSession(SQLModel, table=True):
    """聊天会话主表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(default="新对话", max_length=100)
    config_id: int = Field(foreign_key="llmconfig.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    config: "LLMConfig" = Relationship(back_populates="sessions")
    messages: list["ChatMessage"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"order_by": "ChatMessage.created_at"}
    )


class ChatMessage(SQLModel, table=True):
    """聊天消息明细表"""
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chatsession.id")
    role: str = Field(description="'user' 或 'assistant'")
    content: str = Field(description="消息内容")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    session: "ChatSession" = Relationship(back_populates="messages")