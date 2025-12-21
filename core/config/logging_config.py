# core/config/logging_config.py
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict # Import ConfigDict for v2 configurations
from core.config.base import BaseConfig
import os

class FormatterConfig(BaseModel):
    format: str

class FilterConfig(BaseModel):
    # 支持任意构造函数参数（如 "()": "..."）
    call: str = Field(alias="()", description="可调用对象路径，如 'app.logging.session_context_filter.SessionIdInjectingFilter'")
    # 允许其他自定义字段（如初始化参数）
    model_config = ConfigDict(extra='allow') # 允许额外字段


class HandlerConfig(BaseModel):
    class_: str = Field(alias="class", description="Handler 类路径")
    level: str
    formatter: str
    stream: Optional[str] = None  # 如 ext://sys.stdout
    filename: Optional[str] = None
    maxBytes: Optional[int] = None
    backupCount: Optional[int] = None
    encoding: Optional[str] = None
    filters: Optional[List[str]] = None

    model_config = ConfigDict(populate_by_name=True, extra='forbid') # 更新点1: populate_by_name


class LoggerConfig(BaseModel):
    level: str
    handlers: List[str]
    propagate: bool = False


class LoggingConfig(BaseConfig):
    CONFIG_FILE_NAME = 'logging_config.yaml'

    version: int = 1
    disable_existing_loggers: bool = False

    formatters: Dict[str, FormatterConfig]
    filters: Dict[str, FilterConfig]
    handlers: Dict[str, HandlerConfig]
    loggers: Dict[str, LoggerConfig]

    # 根日志记录器（可选）
    root: Optional[LoggerConfig] = None

    model_config = ConfigDict(extra='forbid')


