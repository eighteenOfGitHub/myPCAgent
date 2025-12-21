# core/config/llm_config.py
from typing import List, Optional
from pydantic import BaseModel, Field
from core.config.base import BaseConfig


class LlmPoolItem(BaseModel):
    name: str
    model: str
    type: str = Field(pattern=r"^(online|local)$")
    tags: List[str] = []
    enabled: bool = True
    api_base: Optional[str] = None
    api_key_env: Optional[str] = None
    priority: int = 0

class RoutingConfig(BaseModel):
    default_mode: str = Field(pattern=r"^(online|local)$")
    selection_strategy: str = "priority"
    retry_on_failure: bool = True
    max_total_attempts: int = 3

class LlmConfig(BaseConfig):
    CONFIG_FILE_NAME = "llm_config.yaml"
    llm_pool: List[LlmPoolItem]
    routing: RoutingConfig