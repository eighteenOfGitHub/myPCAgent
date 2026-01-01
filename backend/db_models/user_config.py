# backend/db_models/user_config.py

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime



class LLMConfig(SQLModel, table=True):
    """大语言模型配置表（API Key 在保存时解析并持久化）"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str = Field(index=True, description="LLM 服务提供商，目前支持 openai 和 ollama", min_length=1)
    model_name: str = Field(description="具体模型名称", min_length=1)
    api_key: str = Field(description="实际可用的 API Key（保存时已从环境变量或用户输入解析并持久化）", min_length=1)
    base_url: Optional[str] = Field(default=None, description="自定义 API 基础 URL")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserPreference(SQLModel, table=True):
    """
    用户全局偏好设置（单例，ID=1）
    用于存储默认行为，如默认 LLM 配置
    """
    
    id: int = Field(default=1, primary_key=True)  # 强制单例
    
    # 默认 LLM 配置 ID（可为空，表示尚未设置）
    default_llm_config_id: Optional[int] = Field(
        default=None,
        foreign_key="llmconfig.id",
        description="默认使用的 LLM 配置 ID"
    )
    
    # 可选：其他偏好字段（预留）
    # theme: str = Field(default="light")
    # language: str = Field(default="zh-CN")

    # Relationship（可选，方便 ORM 查询）
    default_llm_config: Optional["LLMConfig"] = Relationship()