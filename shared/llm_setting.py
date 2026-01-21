from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum

class LLMProvider(str, Enum):
    OPENAI = "OpenAI"
    OLLAMA = "Ollama"

class LLMConfigCreate(BaseModel):
    provider: LLMProvider
    model_name: str
    api_key: str
    base_url: Optional[str] = None

class LLMConfigResponse(BaseModel):
    id: int
    provider: LLMProvider
    model_name: str
    base_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LLMTestResponse(BaseModel):
    success: bool
    message: Optional[str] = None
