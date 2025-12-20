# core/logger.py

"""
日志记录器模块。
提供一个便捷的接口来获取已配置的 Python Logger 实例。
实际的 logging 配置在 core/config.py 中完成。

此模块还包含用于管理日志上下文（如 Session ID）的工具。
"""

import logging
from contextlib import contextmanager
from typing import Optional, Generator

# --- 1. 基础 Logger 获取 ---


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取一个已根据 config/logging_config.yaml 配置好的 Logger 实例。

    Args:
        name (str, optional): Logger 的名称。通常传入 __name__。
                              如果为 None，则返回 root logger。
                              Defaults to None.

    Returns:
        logging.Logger: 配置好的 Logger 实例。
    """
    return logging.getLogger(name)


# --- 2. 便捷别名 ---
getLogger = get_logger  # 符合 logging 模块本身的命名习惯


# --- 3. 上下文管理器 (用于 Session ID) ---

# 假设你有一个模块 app.logging.session_context_filter
# 该模块负责设置和清除 thread-local 的 session_id
# 例如:
# --- app/logging/session_context_filter.py ---
# import threading
#
# _local_state = threading.local()
#
# def set_session_id(sid: str) -> None:
#     _local_state.session_id = sid
#
# def get_session_id() -> str:
#     return getattr(_local_state, 'session_id', 'NoSession')
#
# def clear_session_id() -> None:
#     if hasattr(_local_state, 'session_id'):
#         delattr(_local_state, 'session_id')
# --- End of example session_context_filter.py ---

# 尝试导入 session context filter functions
# 使用局部导入以避免循环导入问题（如果 session_context_filter.py 引用了 logger）
try:
    from app.logging.session_context_filter import set_session_id, clear_session_id
    _HAS_SESSION_CONTEXT = True
except ImportError:
    # 如果 session_context_filter 模块不存在，则禁用相关功能
    def _dummy_set(*args, **kwargs): pass
    def _dummy_clear(*args, **kwargs): pass
    set_session_id = _dummy_set
    clear_session_id = _dummy_clear
    _HAS_SESSION_CONTEXT = False
    # 可以选择打印警告或静默处理
    # import warnings
    # warnings.warn(
    #     "Session context filter (app.logging.session_context_filter) not found. "
    #     "Session ID logging will be disabled.",
    #     ImportWarning
    # )


@contextmanager
def session_context(session_id: str) -> Generator[None, None, None]:
    """
    一个上下文管理器，用于临时设置日志记录的 Session ID。

    当进入 `with` 块时，会设置给定的 session_id；
    当离开 `with` 块时（无论是否因异常），会自动清除 session_id。

    **注意**: 此功能依赖于 `app.logging.session_context_filter` 模块。
             如果该模块不存在，则此上下文管理器无效果。

    Args:
        session_id (str): 要设置的 Session ID。

    Yields:
        None: 该上下文管理器不产生任何值.

    Example:
        >>> from core.logger import get_logger, session_context
        >>> logger = get_logger(__name__)
        >>>
        >>> with session_context("sess_12345"):
        ...     logger.info("这条日志会带有 Session ID")
        >>> logger.info("这条日志不带 Session ID")
    """
    if not _HAS_SESSION_CONTEXT:
        # 如果没有 session context 支持，直接 yield，不做任何事
        yield
        return

    set_session_id(session_id)
    try:
        yield
    finally:
        # 确保即使在 with 块中发生异常也能清除 session_id
        clear_session_id()


# --- 4. (可选/已注释) 自定义 Logger 类 ---
# 如果你需要为所有 logger 添加特定的行为（例如，预定义某些字段），
# 可以继承 logging.Logger。
# 注意：使用自定义 Logger 类需要在 logging 配置中通过 `logging.setLoggerClass()` 指定，
# 或者显式地实例化它。通常直接使用 get_logger() 获取标准 Logger 实例就足够了。

# class CustomLogger(logging.Logger):
#     """
#     (示例) 一个自定义 Logger 类。
#     可以在这里添加特定于项目的方法或覆盖现有方法。
#     """
#     def trace(self, message, *args, **kwargs):
#         """添加一个比 DEBUG 更低级别的 'trace' 日志等级 (如果需要)"""
#         if self.isEnabledFor(logging.DEBUG - 5): # 假设定义了 TRACE 级别
#              self._log(logging.DEBUG - 5, message, args, **kwargs)
#
#     def success(self, message, *args, **kwargs):
#         """添加一个表示成功的日志方法"""
#         # 假设 SUCCESS 级别被定义为 logging.INFO + 5
#         SUCCESS_LEVEL = logging.INFO + 5
#         # 需要在程序启动时注册这个新级别:
#         # logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")
#         if self.isEnabledFor(SUCCESS_LEVEL):
#             self._log(SUCCESS_LEVEL, message, args, **kwargs)

# --- 使用示例 ---
#
# 1. 基本使用:
# ------------------
# from core.logger import get_logger
# logger = get_logger(__name__)
# logger.info("Hello, world!")
# ------------------
#
# 2. 使用 Session Context:
# ------------------
# from core.logger import get_logger, session_context
# logger = get_logger(__name__)
#
# logger.info("Start processing") # No Session ID
#
# with session_context("user-abc-123"):
#     logger.info("User logged in") # Will include Session ID if filter is configured
#     try:
#         # ...some processing...
#         risky_operation()
#     except Exception as e:
#         logger.error("Operation failed", exc_info=True) # Will include Session ID
#
# logger.info("Processing finished") # No Session ID again
# ------------------
