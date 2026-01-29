# shared/user_preference_schemas.py

from pydantic import BaseModel
from typing import Optional

class UserPreferenceResponse(BaseModel):
    """用户偏好设置响应"""
    id: int
    default_llm_config_id: Optional[int] = None

    class Config:
        from_attributes = True

class SetDefaultLLMResponse(BaseModel):
    """设置默认 LLM 响应"""
    status: str
    default_llm_config_id: Optional[int] = None

__all__ = ["UserPreferenceResponse", "SetDefaultLLMResponse"]