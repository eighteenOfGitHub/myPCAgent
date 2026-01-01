# backend/services/llm_setting_service.py
import os
import re
from typing import List, Optional

from sqlmodel import Session, select
from backend.core.database import get_session
from backend.db_models.user_config import LLMConfig


class LLMSettingService:
    """LLM 配置服务（支持多配置，ID=1 为默认活跃配置）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def _is_likely_env_var_name(s: str) -> bool:
        return bool(re.fullmatch(r'^[A-Z][A-Z0-9_]*$', s.strip()))

    def _resolve_api_key(self, input_value: str) -> str:
        clean_input = input_value.strip()
        if not clean_input:
            raise ValueError("API Key 不能为空")
        if self._is_likely_env_var_name(clean_input):
            env_value = os.getenv(clean_input)
            if not env_value:
                raise ValueError(f"环境变量 '{clean_input}' 未设置，请输入有效的 API Key")
            return env_value
        return clean_input

    def create(
        self,
        provider: str,
        model_name: str,
        api_key_input: str,
        base_url: Optional[str] = None,
    ) -> LLMConfig:
        """创建一个新的 LLM 配置（可用于保存多个模型预设）"""
        real_api_key = self._resolve_api_key(api_key_input)
        config = LLMConfig(
            provider=provider.strip(),
            model_name=model_name.strip(),
            api_key=real_api_key,
            base_url=base_url.strip() if base_url else None,
        )
        with get_session() as session:
            session.add(config)
            session.commit()
            session.refresh(config)
            return config

    def update(
        self,
        config_id: int,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key_input: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> LLMConfig:
        """更新指定 ID 的配置"""
        with get_session() as session:
            config = session.get(LLMConfig, config_id)
            if not config:
                raise ValueError(f"LLM 配置 ID {config_id} 不存在")

            updates = {}
            if provider is not None:
                updates["provider"] = provider.strip()
            if model_name is not None:
                updates["model_name"] = model_name.strip()
            if api_key_input is not None:
                updates["api_key"] = self._resolve_api_key(api_key_input)
            if base_url is not None:
                updates["base_url"] = base_url.strip() if base_url.strip() else None

            for key, value in updates.items():
                if key in ["provider", "model_name", "api_key"] and not value:
                    raise ValueError(f"{key} 不能为空")
                setattr(config, key, value)

            session.add(config)
            session.commit()
            session.refresh(config)
            return config

    def get_by_id(self, config_id: int) -> Optional[LLMConfig]:
        """根据 ID 获取配置"""
        with get_session() as session:
            return session.get(LLMConfig, config_id)

    def get_all(self) -> List[LLMConfig]:
        """
        获取所有 LLM 配置（供前端下拉选择）
        示例用途：用户在 Gradio 中选择“使用哪个模型”
        """
        with get_session() as session:
            return session.exec(select(LLMConfig)).all()

    def get_active(self) -> LLMConfig:
        """
        获取当前活跃配置（约定使用 ID=1）
        聊天、Agent 等服务默认使用此配置
        """
        config = self.get_by_id(1)
        if not config:
            raise RuntimeError("尚未配置默认 LLM（ID=1），请先创建一个配置")
        return config

    def delete(self, config_id: int) -> bool:
        """
        删除指定配置
        ⚠️ 若删除 ID=1，可能导致聊天服务报错（除非重建）
        """
        with get_session() as session:
            config = session.get(LLMConfig, config_id)
            if not config:
                return False
            session.delete(config)
            session.commit()
            return True