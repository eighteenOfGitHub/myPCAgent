# backend/services/default_setting_service.py
from typing import Optional
from sqlmodel import Session
from backend.core.database import get_db_session
from backend.db_models.setting_models import DefaultSetting
import logging

logger = logging.getLogger(__name__)


class DefaultSettingService:
    """默认设置服务（全局单例，ID=1）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _ensure_exists(self, session: Session) -> DefaultSetting:
        """确保默认设置记录存在（ID=1），不存在则创建"""
        pref = session.get(DefaultSetting, 1)
        if not pref:
            pref = DefaultSetting(id=1)
            session.add(pref)
            session.commit()
            session.refresh(pref)
            logger.info("默认设置记录已初始化")
        return pref

    def get_setting(self) -> DefaultSetting:
        """获取当前默认设置（自动初始化若不存在）"""
        with get_db_session() as session:
            pref = session.get(DefaultSetting, 1)
            if not pref:
                pref = DefaultSetting(id=1)
                session.add(pref)
                session.commit()
                session.refresh(pref)
                logger.info("默认设置已初始化，ID=1")
            return pref

    def update_default_llm_config(self, config_id: Optional[int]) -> DefaultSetting:
        """
        更新默认 LLM 配置 ID
        :param config_id: LLMConfig 的 ID，None 表示清空默认
        """
        with get_db_session() as session:
            pref = self._ensure_exists(session)
            pref.default_llm_config_id = config_id
            session.add(pref)
            session.commit()
            session.refresh(pref)
            logger.info("默认 LLM 配置已更新。config_id=%s", config_id)
            return pref

    def update_setting(
        self,
        default_llm_config_id: Optional[int] = None,
    ) -> DefaultSetting:
        """
        批量更新默认设置（预留扩展）
        """
        with get_db_session() as session:
            pref = self._ensure_exists(session)
            if default_llm_config_id is not None:
                pref.default_llm_config_id = default_llm_config_id
            session.add(pref)
            session.commit()
            session.refresh(pref)
            return pref

    def reset_to_default(self) -> DefaultSetting:
        """重置默认设置为初始状态（仅保留 ID=1，清空所有字段）"""
        with get_db_session() as session:
            pref = DefaultSetting(id=1)
            session.merge(pref)
            session.commit()
            session.refresh(pref)
            logger.info("默认设置已重置")
            return pref