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
from backend.db_models.setting_models import LLMSetting

logger = logging.getLogger(__name__)

class LLMSettingService:
    """LLM 配置服务（支持多配置，带缓存机制）"""
    _instance = None
    _cached_configs: Optional[List[LLMSetting]] = None
    _cached_configs_dict: Optional[Dict[int, LLMSetting]] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化时从数据库加载配置到缓存"""
        if self._cached_configs is None:
            self._load_from_database()

    def _load_from_database(self) -> None:
        """从数据库加载所有 LLM 配置到缓存"""
        with get_db_session() as session:
            configs = session.exec(select(LLMSetting)).all()
            # 创建独立的对象副本（脱离 session）
            self._cached_configs = [
                LLMSetting(
                    id=cfg.id,
                    provider=cfg.provider,
                    model_name=cfg.model_name,
                    api_key=cfg.api_key,
                    base_url=cfg.base_url
                )
                for cfg in configs
            ]
            # 构建字典索引
            self._cached_configs_dict = {cfg.id: cfg for cfg in self._cached_configs}
            logger.info("LLM 配置已加载到缓存，共 %d 条", len(self._cached_configs))

    @staticmethod
    def _is_likely_env_var_name(s: str) -> bool:
        return bool(re.fullmatch(r'^[A-Z][A-Z0-9_]*$', s.strip()))

    def create(
        self,
        provider: str,
        model_name: str,
        api_key_input: str,
        base_url: Optional[str] = None,
    ) -> LLMSetting:
        """创建一个新的 LLM 配置（同步数据库和缓存）"""
        # 修改：当 provider 为 ollama 时，允许 api_key_input 为空
        if not api_key_input and provider.lower() != "ollama":
            raise ValueError("API Key 不能为空")

        # 如果 api_key_input 为空且 provider 是 ollama，则不解析，直接设为 None 或空字符串
        if not api_key_input and provider.lower() == "ollama":
            logger.debug("Ollama provider detected, skipping API key resolution.")
        else:
            decrypted_api_key = decrypt_text(api_key_input)
            if not decrypted_api_key and provider.lower() != "ollama":
                raise ValueError("API Key 不能为空")

        config = LLMSetting(
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

        # 同步更新缓存
        new_cached_config = LLMSetting(
            id=config.id,
            provider=config.provider,
            model_name=config.model_name,
            api_key=config.api_key,
            base_url=config.base_url
        )
        self._cached_configs.append(new_cached_config)
        self._cached_configs_dict[config.id] = new_cached_config

        return new_cached_config

    def get_by_id(self, config_id: int) -> Optional[LLMSetting]:
        """根据 ID 获取配置（从缓存读取）"""
        if self._cached_configs is None:
            self._load_from_database()
        
        config = self._cached_configs_dict.get(config_id)
        if config is None:
            logger.debug("LLM configuration not found for config_id=%d", config_id)
        return config

    def list_basic_configs(self) -> List[Dict[str, Any]]:
        """供前端下拉选择：仅返回 id / provider / model_name（从缓存读取）"""
        if self._cached_configs is None:
            self._load_from_database()
        
        result = [
            {"id": cfg.id, "provider": cfg.provider, "model_name": cfg.model_name}
            for cfg in self._cached_configs
        ]
        logger.debug("Retrieved basic LLM configurations. Count: %d", len(result))
        return result

    def get_all(self) -> List[LLMSetting]:
        """获取所有 LLM 配置（完整字段，从缓存读取）"""
        if self._cached_configs is None:
            self._load_from_database()
        
        logger.debug("Retrieved all LLM configurations. Count: %d", len(self._cached_configs))
        return self._cached_configs.copy()  # 返回副本避免外部修改

    def delete(self, config_id: int) -> bool:
        """删除指定配置（同步数据库和缓存）"""
        with get_db_session() as session:
            config = session.get(LLMSetting, config_id)
            if not config:
                logger.warning("Attempted to delete non-existent LLM configuration. config_id=%d", config_id)
                return False
            session.delete(config)
            session.commit()
        
        logger.info("LLM configuration deleted successfully. config_id=%d", config_id)
        
        # 同步更新缓存
        if config_id in self._cached_configs_dict:
            del self._cached_configs_dict[config_id]
            self._cached_configs = [cfg for cfg in self._cached_configs if cfg.id != config_id]
        
        return True

    # --- 新增：便捷访问接口 ---
    def get_config_count(self) -> int:
        """获取配置总数"""
        if self._cached_configs is None:
            self._load_from_database()
        return len(self._cached_configs)

    def get_configs_by_provider(self, provider: str) -> List[LLMSetting]:
        """根据 provider 筛选配置"""
        if self._cached_configs is None:
            self._load_from_database()
        
        provider_lower = provider.lower()
        return [cfg for cfg in self._cached_configs if cfg.provider.lower() == provider_lower]

    def get_decrypted_api_key(self, config_id: int) -> Optional[str]:
        """获取解密后的 API Key（用于其他服务）"""
        config = self.get_by_id(config_id)
        if not config or not config.api_key:
            return None
        
        try:
            return decrypt_text(config.api_key)
        except Exception as e:
            logger.error("Failed to decrypt API key for config_id=%d: %s", config_id, e)
            return None

    def reload_from_database(self) -> List[LLMSetting]:
        """手动重新加载数据库中的所有配置到缓存"""
        self._load_from_database()
        logger.info("已从数据库重新加载 LLM 配置")
        return self._cached_configs.copy()

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
                real_api_key = decrypted_api_key

            # 2. 根据 provider 创建对应的 LLM 实例
            llm: Optional[BaseLanguageModel] = None
            provider_lower = provider.lower()
            if provider_lower == "openai":
                llm = ChatOpenAI(
                    model=model_name,
                    openai_api_key=real_api_key,
                    openai_api_base=base_url, # 支持自定义 base_url
                    timeout=30
                )
            elif provider_lower == "ollama":
                # 对于 Ollama，api_key 通常不需要，但 base_url 是必须的
                ollama_base = base_url or "http://localhost:11434"
                # 注意：ChatOllama 默认不使用 api_key，我们传递的是 base_url 和 model
                llm = ChatOllama(
                    model=model_name,
                    base_url=ollama_base,
                    timeout=30
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