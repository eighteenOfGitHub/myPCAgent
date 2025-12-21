# core/config/base.py
"""
BaseConfig: 所有配置类的基类。
提供统一的 YAML 加载、校验与保存能力。
"""

import yaml
from pathlib import Path
from typing import Any, ClassVar, Dict
from pydantic import BaseModel, ValidationError


class BaseConfig(BaseModel):
    """
    配置基类，所有模块配置应继承此类。

    子类必须定义：
        CONFIG_FILE_NAME: ClassVar[str] = "xxx.yaml"

    示例：
        class LlmConfig(BaseConfig):
            CONFIG_FILE_NAME = "llm.yaml"
            ...
    """

    # 子类必须指定对应的 YAML 文件名（相对于 config 目录）
    CONFIG_FILE_NAME: ClassVar[str]

    class Config:
        # 允许额外字段（可选，根据需求开启）
        extra = "forbid"  # 推荐：禁止未声明字段，提高配置安全性

    @classmethod
    def load(cls, config_dir: str | Path = "config") -> "BaseConfig":
        """
        从指定目录加载 YAML 配置文件。

        Args:
            config_dir: 配置文件所在目录（默认 "config"）

        Returns:
            配置实例

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置格式无效或校验失败
        """
        config_path = Path(config_dir) / cls.CONFIG_FILE_NAME

        if not config_path.exists():
            raise FileNotFoundError(
                f"配置文件未找到: {config_path.resolve()}\n"
                f"请确保在 '{config_dir}' 目录下存在 '{cls.CONFIG_FILE_NAME}'"
            )

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)
                if raw_data is None:
                    raw_data = {}
                if not isinstance(raw_data, dict):
                    raise ValueError("YAML 根节点必须是字典（mapping）")
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 解析失败 ({config_path}): {e}")

        try:
            return cls(**raw_data)
        except ValidationError as e:
            raise ValueError(
                f"配置校验失败 ({config_path})。请检查字段类型和必填项:\n{e}"
            ) from e

    def save(self, config_dir: str | Path = "config") -> None:
        """
        将当前配置保存为 YAML 文件（用于生成默认配置模板）。

        Args:
            config_dir: 保存目录（默认 "config"）
        """
        config_path = Path(config_dir)
        config_path.mkdir(parents=True, exist_ok=True)
        output_file = config_path / self.CONFIG_FILE_NAME

        # 排除默认值，使配置更简洁
        data = self.model_dump(exclude_defaults=True)

        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(
                data,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.CONFIG_FILE_NAME})"