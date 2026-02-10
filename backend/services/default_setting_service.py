# backend/services/default_setting_service.py
from typing import Optional
from sqlmodel import Session
from backend.core.database import get_db_session
from backend.db_models.setting_models import DefaultSetting
import logging

logger = logging.getLogger(__name__)


class DefaultSettingService:
    """默认设置服务（全局单例，ID=1）- 带缓存机制"""

    _instance = None
    _cached_setting: Optional[DefaultSetting] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化时从数据库加载设置到缓存"""
        if self._cached_setting is None:
            self._load_from_database()

    def _load_from_database(self) -> None:
        """从数据库加载默认设置到缓存"""
        with get_db_session() as session:
            pref = session.get(DefaultSetting, 1)
            if not pref:
                pref = DefaultSetting(id=1)
                session.add(pref)
                session.commit()
                session.refresh(pref)
                logger.info("默认设置记录已初始化，ID=1")
            # 创建一个新的独立对象用于缓存（脱离 session）
            self._cached_setting = DefaultSetting(
                id=pref.id,
                default_llm_config_id=pref.default_llm_config_id
            )
            logger.info("默认设置已加载到缓存")

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
        """获取当前默认设置（从缓存读取）"""
        if self._cached_setting is None:
            self._load_from_database()
        return self._cached_setting

    def update_default_llm_config(self, config_id: Optional[int]) -> DefaultSetting:
        """
        更新默认 LLM 配置 ID（同步数据库和缓存）
        :param config_id: LLMConfig 的 ID，None 表示清空默认
        """
        with get_db_session() as session:
            pref = self._ensure_exists(session)
            pref.default_llm_config_id = config_id
            session.add(pref)
            session.commit()
            session.refresh(pref)
            logger.info("默认 LLM 配置已更新。config_id=%s", config_id)
            
            # 同步更新缓存
            self._cached_setting.default_llm_config_id = config_id
            
            return self._cached_setting

    def update_setting(
        self,
        default_llm_config_id: Optional[int] = None,
    ) -> DefaultSetting:
        """
        批量更新默认设置（同步数据库和缓存）
        """
        with get_db_session() as session:
            pref = self._ensure_exists(session)
            if default_llm_config_id is not None:
                pref.default_llm_config_id = default_llm_config_id
            session.add(pref)
            session.commit()
            session.refresh(pref)
            
            # 同步更新缓存
            if default_llm_config_id is not None:
                self._cached_setting.default_llm_config_id = default_llm_config_id
            
            return self._cached_setting

    def reset_to_default(self) -> DefaultSetting:
        """重置默认设置为初始状态（同步数据库和缓存）"""
        with get_db_session() as session:
            pref = DefaultSetting(id=1)
            session.merge(pref)
            session.commit()
            session.refresh(pref)
            logger.info("默认设置已重置")
            
            # 重新加载缓存
            self._load_from_database()
            
            return self._cached_setting

    def reload_from_database(self) -> DefaultSetting:
        """手动重新加载数据库中的设置到缓存（用于外部修改后的同步）"""
        self._load_from_database()
        logger.info("已从数据库重新加载默认设置")
        return self._cached_setting