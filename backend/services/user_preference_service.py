# backend/services/user_preference_service.py
from typing import Optional
from sqlmodel import Session
from backend.core.database import get_db_session
from backend.db_models.user_config_models import UserPreference


class UserPreferenceService:
    """用户偏好设置服务（全局单例，ID=1）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _ensure_exists(self, session: Session) -> UserPreference:
        """确保偏好记录存在（ID=1），不存在则创建"""
        pref = session.get(UserPreference, 1)
        if not pref:
            pref = UserPreference(id=1)
            session.add(pref)
            session.commit()
            session.refresh(pref)
        return pref

    def get_preference(self) -> UserPreference:
        """获取当前用户偏好（自动初始化若不存在）"""
        with get_db_session() as session:
            pref = session.get(UserPreference, 1)
            if not pref:
                pref = UserPreference(id=1)
                session.add(pref)
                session.commit()
                session.refresh(pref)
            return pref

    def update_default_llm_config(self, config_id: Optional[int]) -> UserPreference:
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
            return pref

    def update_preference(
        self,
        default_llm_config_id: Optional[int] = None,
        # 可在此扩展其他字段，如 theme, language 等
    ) -> UserPreference:
        """
        批量更新偏好设置（预留扩展）
        """
        with get_db_session() as session:
            pref = self._ensure_exists(session)
            if default_llm_config_id is not None:
                pref.default_llm_config_id = default_llm_config_id
            # 示例：if theme is not None: pref.theme = theme
            session.add(pref)
            session.commit()
            session.refresh(pref)
            return pref

    def reset_to_default(self) -> UserPreference:
        """重置偏好为初始状态（仅保留 ID=1，清空所有字段）"""
        with get_db_session() as session:
            pref = UserPreference(id=1)  # 覆盖现有
            session.merge(pref)  # 使用 merge 安全更新
            session.commit()
            session.refresh(pref)
            return pref