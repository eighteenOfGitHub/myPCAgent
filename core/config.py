# core/config.py

"""
应用配置管理模块。
负责加载 YAML 配置文件、初始化日志系统，并提供全局配置访问接口。
"""

import os
import sys
import yaml
import logging.config
from pathlib import Path
from typing import Any, Dict, Optional

# --- 0. 彩色打印辅助 (可选) ---
try:
    from colorama import init, Fore, Style
    init(autoreset=True)  # 自动恢复默认颜色
    USE_COLOR = True
except ImportError:
    # 如果没有安装 colorama，则定义空样式
    class DummyStyle:
        def __getattribute__(self, name):
            return ""
    Fore = DummyStyle()
    Style = DummyStyle()
    USE_COLOR = False


def c_print(message: str, color: str = "", prefix: str = "") -> None:
    """带颜色和前缀的打印函数"""
    if USE_COLOR and color:
        print(f"{prefix}{color}{message}{Style.RESET_ALL}")
    else:
        print(f"{prefix}{message}")


# --- 1. 定义常量 ---
# 获取项目根目录 (假设 config.py 在 core 目录下，core 在项目根目录下)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# 配置文件路径
CONFIG_FILE_PATH = PROJECT_ROOT / "config" / "config.yaml"
LOGGING_CONFIG_FILE_PATH = PROJECT_ROOT / "config" / "logging_config.yaml"

# --- 2. 全局变量用于存储配置 ---
_settings: Optional[Dict[str, Any]] = None
_logger_initialized: bool = False


def _load_yaml_config(file_path: Path) -> Dict[str, Any]:
    """内部辅助函数：加载单个 YAML 配置文件"""
    if not file_path.exists():
        raise FileNotFoundError(f"配置文件未找到: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {{}}  # Handle empty files
    except yaml.YAMLError as e:
        raise ValueError(f"解析 YAML 文件 '{file_path}' 时出错: {e}")
    except Exception as e:
        raise RuntimeError(f"读取配置文件 '{file_path}' 时发生未知错误: {e}")


def load_settings() -> Dict[str, Any]:
    """
    加载主应用配置 (config.yaml)。
    Returns:
        dict: 解析后的配置字典。
    Raises:
        RuntimeError: 如果配置加载失败。
    """
    global _settings
    if _settings is not None:
        return _settings  # 避免重复加载

    try:
        config_data = _load_yaml_config(CONFIG_FILE_PATH)
        _settings = config_data
        c_print(f"✅ 主配置文件加载成功: {CONFIG_FILE_PATH}", Fore.GREEN)
        return _settings
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        # 致命错误，无法继续
        c_print(f"❌ 致命错误: 无法加载主配置文件: {e}", Fore.RED, prefix="🚨 ")
        raise RuntimeError(f"配置加载失败: {e}")


def setup_logging() -> None:
    """根据 logging_config.yaml 初始化 Python logging"""
    global _logger_initialized
    if _logger_initialized:
        return  # 避免重复初始化

    try:
        logging_config = _load_yaml_config(LOGGING_CONFIG_FILE_PATH)

        # 确保 logs 目录存在
        logs_dir = PROJECT_ROOT / "logs"
        logs_dir.mkdir(exist_ok=True)

        # 应用 logging 配置
        logging.config.dictConfig(logging_config)
        _logger_initialized = True
        # 注意：这里不能直接调用 get_logger，因为 logger 可能还没完全初始化
        # 我们使用标准 logging 获取 logger 来打印这条消息
        logging.getLogger(__name__).info("✅ Logging 系统已初始化")
        c_print(f"✅ 日志系统初始化成功 (配置文件: {LOGGING_CONFIG_FILE_PATH})", Fore.GREEN)

    except (FileNotFoundError, ValueError, RuntimeError) as e:
        msg = f"⚠️ 警告: 无法加载 logging 配置，将使用默认 logging 设置: {e}"
        c_print(msg, Fore.YELLOW, prefix="⚠️ ")
        # Fallback to basic config if loading fails
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.warning("Logging 配置加载失败，使用基础配置", exc_info=True)


def get_logger(name: str) -> logging.Logger:
    """
    获取一个配置好的 Logger 实例。
    Args:
        name (str): Logger 的名称，通常使用 __name__。
    Returns:
        logging.Logger: 配置好的 Logger 实例。
    """
    # 确保 logging 已初始化（最好在应用启动时主动调用 setup_logging）
    # 但为了保险起见，这里也尝试初始化一次
    if not _logger_initialized:
        # 可以选择警告或静默处理
        pass  # 或者调用 setup_logging()，但这可能导致重复调用
    return logging.getLogger(name)


def get_config_value(key_path: str, default: Any = None) -> Any:
    """
    (可选便利函数) 根据点分隔的键路径获取嵌套配置值。
    例如: get_config_value('app.name') 或 get_config_value('models.default')
    Args:
        key_path (str): 点分隔的键路径，如 'database.chat_history_path'。
        default (Any): 如果找不到键，则返回的默认值。
    Returns:
        Any: 配置值或默认值。
    """
    settings = load_settings()
    keys = key_path.split('.')
    current = settings
    try:
        for k in keys:
            current = current[k]
        return current
    except KeyError:
        return default


# --- 4. 应用启动时的初始化逻辑 ---
# 旧版代码曾在此处放置了模块导入时自动调用 `load_settings()` 和 `setup_logging()` 的逻辑：
#
# try:
#     load_settings()
#     setup_logging()
# except RuntimeError as e:
#     c_print(f"🚨 应用初始化失败: {e}", Fore.RED, prefix="💥 ")
#     sys.exit(1)
#
# 移除原因：
# 1.  模块导入副作用：在模块导入时执行 I/O 操作（如读取文件）和修改全局状态，
#     会使模块行为难以预测，增加调试复杂度。
# 2.  测试困难：自动初始化会干扰单元测试。测试框架导入此模块时会触发初始化，
#     导致 mock 设置复杂化，容易出现如 `TypeError: ... missing 1 required positional argument`
#     之类的难以追踪的错误。
# 3.  缺乏灵活性：应用入口点无法控制初始化时机。
# 推荐做法：
# 在应用程序的主入口点（例如 main.py 或 app.py）显式调用初始化函数：
#   import core.config
#   ...
#   core.config.initialize_app()
# 这样做提高了代码的可测试性、清晰度和可控性。
def initialize_app():
    """Convenience function to load settings and setup logging."""
    try:
        load_settings()
        setup_logging()
    except RuntimeError as e:
        c_print(f"🚨 应用初始化失败: {e}", Fore.RED, prefix="💥 ")
        raise  # Re-raise to let caller decide how to handle it

# --- 5. (可选) 提供一个直接访问配置的属性 ---


def get_settings() -> Dict[str, Any]:
    """获取完整的配置字典"""
    return load_settings()


settings = get_settings  # 允许通过 core.config.settings 访问
