# core/context.py
"""
应用上下文模块。
负责集中管理应用程序的核心组件实例，如数据库连接、LLM路由器、日志记录器等。
使用单例模式确保全局唯一性，并提供延迟初始化机制。
"""

import threading
from typing import Optional, TYPE_CHECKING
import logging
# 为了解决循环导入问题，当仅用作类型提示时才导入
if TYPE_CHECKING:
    from core.database import SQLiteDatabase
    from core.llm_router import LLMAgentRouter
    from core.config.env_config import EnvConfig
    from core.config.llm_config import LlmConfig


class AppContext:
    """
    应用上下文单例类。
    管理和持有应用生命周期内的共享资源，如配置、数据库、LLM等。
    """

    _instance: Optional['AppContext'] = None
    _lock = threading.Lock()
    _instance_created: bool = False

    def __init__(self):
        """私有构造函数，防止直接实例化。"""
        if AppContext._instance_created:
            raise RuntimeError("AppContext is a singleton. Use AppContext.get_instance().")

        # --- 核心组件实例 ---
        self.env_config: Optional['EnvConfig'] = None
        self.logger: Optional['logging.Logger'] = None
        self.db: Optional['SQLiteDatabase'] = None
        self.llm_router: Optional['LLMAgentRouter'] = None

        # --- 业务初始化标志---
        self._components_initialized: bool = False  # 表示业务组件是否已注入

        # --- 初始化状态标志 ---
        self._db_initialized: bool = False
        self._llm_router_initialized: bool = False

        # 标记初始化完成
        AppContext._instance_created  = True

    @classmethod
    def get_instance(cls) -> 'AppContext':
        """
        获取 AppContext 的单例实例。
        使用双重检查锁定保证线程安全。
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def is_ready(self) -> bool:
        """
        检查 AppContext 是否已完成初始化。
        """
        return self._instance_created 

    def initialize_components(
        self,
        logger: 'logging.Logger',
        env_config: 'EnvConfig',
        llm_config: 'LlmConfig'
    ) -> None:
        """
        使用外部提供的 logger 和已加载的配置来初始化核心组件。
        这个方法应该在配置加载和 logger 设置之后调用。

        Args:
            logger: 已经配置好的 Python logger 实例。
            env_config: 已加载的应用环境配置。
            llm_config: 已加载的 LLM 配置。
        """
        if self._components_initialized:
            # 可以选择抛出异常或静默返回
            # raise RuntimeError("AppContext components are already initialized.")
            logger.warning("AppContext components are already initialized. Skipping re-initialization.")
            return

        self.logger = logger
        self.env_config = env_config
        self.llm_config = llm_config

        self.logger.info("Starting AppContext component initialization...")

        # --- 1. 初始化数据库 ---
        # 注意：数据库初始化依赖于 logger，所以 logger 必须先传入
        if getattr(self.env_config, 'database_enabled', True): # 默认启用
            try:
                db_path = getattr(self.env_config, 'database_path', 'data/app.db')
                # 直接实例化 SQLiteDatabase，传入 logger
                from core.database import SQLiteDatabase
                self.db = SQLiteDatabase(db_path=db_path, logger=self.logger)
                self._db_initialized = True
                self.logger.info(f"✅ Database initialized at '{db_path}'.")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize database: {e}", exc_info=True)
                # 根据应用策略，可以选择继续运行（无DB）或终止
                # raise RuntimeError(f"Critical failure initializing database: {e}") from e
        else:
            self.logger.info("⏭️ Database is disabled via configuration.")

        # --- 2. 初始化 LLM Router ---
        if getattr(self.llm_config, 'enabled', True): # 假设 LlmConfig 里有个 enabled 字段
            try:
                # 实例化 LLMAgentRouter，传入 logger
                from core.llm_router import LLMAgentRouter
                self.llm_router = LLMAgentRouter(llm_config=self.llm_config, logger=self.logger)
                self._llm_router_initialized = True
                self.logger.info("✅ LLM Router initialized.")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize LLM Router: {e}", exc_info=True)
                # 根据应用策略处理
        else:
            self.logger.info("⏭️ LLM Router is disabled via configuration.")

        # --- 可在此处初始化更多核心组件 ---
        

        self._components_initialized = True
        self.logger.info("🏁 AppContext component initialization complete.")

    # --- Getter Methods for Components ---
    # 提供受控访问方式，明确组件可能未初始化

    def get_logger(self) -> 'logging.Logger':
        """获取 logger 实例。"""
        if self.logger is None:
            raise RuntimeError("Logger has not been initialized in AppContext.")
        return self.logger

    def get_database(self) -> 'SQLiteDatabase':
        """获取数据库实例。"""
        if not self._db_initialized or self.db is None:
            raise RuntimeError("Database has not been initialized or is disabled.")
        return self.db

    def get_llm_router(self) -> 'LLMAgentRouter':
        """获取 LLM Router 实例。"""
        if not self._llm_router_initialized or self.llm_router is None:
            raise RuntimeError("LLM Router has not been initialized or is disabled.")
        return self.llm_router

    # --- 可选：上下文管理器支持 ---
    # def __enter__(self):
    #     return self
    
    def close(self):
        try:
            if self.logger is not None:
                self.logger.info("🏁 AppContext cleaned up.")
        except Exception:
            # 在 shutdown 阶段，任何日志失败都应静默忽略
            pass

        # 清理真正关键的资源（如数据库连接）
        if self.db:
            try:
                self.db.close()
            except Exception:
                pass  # 同样，不抛异常

# --- 便捷函数 ---
def get_app_context() -> AppContext:
    """
    获取 AppContext 单例实例的便捷函数。
    """
    return AppContext.get_instance()