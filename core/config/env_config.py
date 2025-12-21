# core/config/env_config.py

from pydantic import BaseModel, Field
from typing import ClassVar
from core.config.base import BaseConfig


class EnvConfig(BaseConfig):
    CONFIG_FILE_NAME: ClassVar[str] = "env_config.yaml"

    # 应用基本信息
    name: str = Field(default="PCAgent")
    version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)