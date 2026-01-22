# backend/services/llm_setting_service.py
import os
import re
from typing import List, Optional, Dict, Any
import logging

from sqlmodel import Session, select
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from shared.crypto import decrypt_text

from backend.core.database import get_db_session
from backend.db_models.user_config import LLMConfig

logger = logging.getLogger(__name__)

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
        if self._is_likely_env_var_name(clean_input):
            env_value = os.getenv(clean_input)
            if not env_value:
                raise ValueError(f"环境变量 '{clean_input}' 未设置，请输入有效的 API Key")
            logger.debug("Resolved API key from environment variable: %s", clean_input)
            return env_value
        logger.debug("Using provided API key directly (not an env var).")
        return clean_input

    def create(
        self,
        provider: str,
        model_name: str,
        api_key_input: str,
        base_url: Optional[str] = None,
    ) -> LLMConfig:
        """创建一个新的 LLM 配置（可用于保存多个模型预设）"""
        # 修改：当 provider 为 ollama 时，允许 api_key_input 为空
        if not api_key_input and provider.lower() != "ollama":
            raise ValueError("API Key 不能为空")

        # 如果 api_key_input 为空且 provider 是 ollama，则不解析，直接设为 None 或空字符串
        if not api_key_input and provider.lower() == "ollama":
            real_api_key = api_key_input
            logger.debug("Ollama provider detected, skipping API key resolution.")
        else:
            decrypted_api_key = decrypt_text(api_key_input)
            if not decrypted_api_key and provider.lower() != "ollama":
                raise ValueError("API Key 不能为空")
            real_api_key = (
                self._resolve_api_key(decrypted_api_key)
                if decrypted_api_key
                else decrypted_api_key
            )

        config = LLMConfig(
            provider=provider.strip(),
            model_name=model_name.strip(),
            api_key=api_key_input,  # store ciphertext
            base_url=base_url.strip() if base_url else None,
        )
        
        with get_db_session() as session:
            session.add(config)
            session.commit()
            session.refresh(config)
        
        logger.info(
            "New LLM configuration created successfully. "
            "config_id=%d, provider=%s, model_name=%s",
            config.id,
            config.provider,
            config.model_name
        )

        return config

    def get_by_id(self, config_id: int) -> Optional[LLMConfig]:
        """根据 ID 获取配置"""
        with get_db_session() as session:
            config = session.get(LLMConfig, config_id)
            if config is None:
                logger.debug("LLM configuration not found for config_id=%d", config_id)
            return config

    def list_basic_configs(self) -> List[Dict[str, Any]]:
        """供前端下拉选择：仅返回 id / provider / model_name"""
        with get_db_session() as session:
            rows = session.exec(
                select(LLMConfig.id, LLMConfig.provider, LLMConfig.model_name)
            ).all()
            logger.debug("Retrieved basic LLM configurations. Count: %d", len(rows))
            return [
                {"id": row[0], "provider": row[1], "model_name": row[2]}
                for row in rows
            ]

    def get_all(self) -> List[LLMConfig]:
        """获取所有 LLM 配置（完整字段）"""
        with get_db_session() as session:
            configs = session.exec(select(LLMConfig)).all()
            logger.debug("Retrieved all LLM configurations. Count: %d", len(configs))
            return configs

    def delete(self, config_id: int) -> bool:
        """ 删除指定配置 """
        with get_db_session() as session:
            config = session.get(LLMConfig, config_id)
            if not config:
                logger.warning("Attempted to delete non-existent LLM configuration. config_id=%d", config_id)
                return False
            session.delete(config)
            session.commit()
        
        logger.info("LLM configuration deleted successfully. config_id=%d", config_id)
        return True

    # --- 新增：使用 langchain 测试连通性方法 ---
    def test_connection(
        self,
        provider: str,
        model_name: str,
        api_key_input: str,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """ 使用 langchain 测试 LLM 连通性
        Returns:
            {"success": bool, "message": str}
        """
        try:
            # 修改：当 provider 为 ollama 时，允许 api_key_input 为空
            if not api_key_input and provider.lower() != "ollama":
                raise ValueError("API Key 不能为空")

            # 1. 解析 API Key
            # 如果 api_key_input 为空且 provider 是 ollama，则不解析，直接使用
            if not api_key_input and provider.lower() == "ollama":
                real_api_key = api_key_input
            else:
                decrypted_api_key = decrypt_text(api_key_input)
                if not decrypted_api_key and provider.lower() != "ollama":
                    raise ValueError("API Key 不能为空")
                real_api_key = (
                    self._resolve_api_key(decrypted_api_key)
                    if decrypted_api_key
                    else decrypted_api_key
                )

            # 2. 根据 provider 创建对应的 LLM 实例
            llm: Optional[BaseLanguageModel] = None
            provider_lower = provider.lower()
            if provider_lower == "openai":
                llm = ChatOpenAI(
                    model=model_name,
                    openai_api_key=real_api_key,
                    openai_api_base=base_url, # 支持自定义 base_url
                    timeout=10
                )
            elif provider_lower == "ollama":
                # 对于 Ollama，api_key 通常不需要，但 base_url 是必须的
                ollama_base = base_url or "http://localhost:11434"
                # 注意：ChatOllama 默认不使用 api_key，我们传递的是 base_url 和 model
                llm = ChatOllama(
                    model=model_name,
                    base_url=ollama_base,
                    timeout=10
                )
            else:
                error_msg = f"不支持的 Provider: {provider}"
                logger.error(error_msg)
                return {"success": False, "message": error_msg}

            if not llm:
                error_msg = "初始化 LLM 客户端失败"
                logger.error(error_msg)
                return {"success": False, "message": error_msg}

            # 3. 发送一个简单的请求来测试
            # 使用 invoke 方法调用模型，这是一个通用方法
            logger.debug("Testing connection to LLM. provider=%s, model=%s", provider, model_name)
            response = llm.invoke("Hello, please reply with 'Hello, World!' in 10 words or less.")

            # 4. 检查响应
            if response and hasattr(response, 'content') and response.content:
                success_msg = f"{provider} 连接测试成功！"
                logger.info(success_msg)
                return {"success": True, "message": success_msg}
            else:
                fail_msg = f"{provider} 连接测试失败，未收到有效响应。"
                logger.warning(fail_msg)
                return {"success": False, "message": fail_msg}
        except Exception as e:
            # langchain 的错误通常比较通用，可以根据 e.__class__.__name__ 进行细分
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                error_msg = "API Key 认证失败，请检查 Key 是否正确。"
            elif "429" in error_msg or "Rate limit" in error_msg:
                error_msg = "API 调用频率超限，请稍后再试。"
            elif "Connection" in error_msg or "timeout" in error_msg.lower():
                error_msg = f"连接 {provider} 服务器失败，请检查网络或 Base URL。"
            full_error_msg = f"测试连接时发生错误: {error_msg}"
            logger.error(full_error_msg, exc_info=True)
            return {"success": False, "message": full_error_msg}