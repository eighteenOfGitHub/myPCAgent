# tests/test_config.py
"""
Tests for the core.config module.
"""

from core.config import get_settings
from core.config import load_settings
from io import StringIO
import io
import sys
import yaml
import pytest
from unittest.mock import patch, mock_open, MagicMock
import pathlib
# 以后写测试一定要在函数里导入目标函数，woc，外面麻烦的要死，体会到堆石山了
# 要不然 mock 跟不存在一样的
import core.config
from unittest import mock
from contextlib import redirect_stdout
import logging
from pathlib import Path

# --- Fixtures for common setup ---


@pytest.fixture
def valid_config_data():
    """Provides a sample valid configuration dictionary."""
    return {
        'app': {'name': 'TestApp', 'version': '1.0.0', 'debug': True},
        'database': {'chat_history_path': '/tmp/test_chat.db'},
        'model_defaults': {'temperature': 0.5, 'max_tokens': 1024},
        'models': {
            'available': [
                {'id': 'test_model_1', 'name': 'test-model',
                    'provider': 'test_provider'}
            ],
            'default': 'test_model_1'
        }
    }


@pytest.fixture
def valid_logging_config_data():
    """Provides a sample valid logging configuration dictionary."""
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'}
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'simple',
                'stream': 'ext://sys.stdout'
            }
        },
        'loggers': {
            '': {  # root logger
                'level': 'DEBUG',
                'handlers': ['console']
            }
        }
    }


# --- Tests for internal helper functions (_load_yaml_config) ---

class TestLoadYamlConfig:

    def test_load_yaml_config_success(self, valid_config_data):
        """Test _load_yaml_config loads data correctly."""
        yaml_content = yaml.dump(valid_config_data)
        mock_file_path = pathlib.Path("/fake/path/config.yaml")
        with patch("builtins.open", mock_open(read_data=yaml_content)) as mock_file:
            with patch("core.config.Path.exists", return_value=True):
                result = core.config._load_yaml_config(mock_file_path)

        mock_file.assert_called_once_with(
            mock_file_path, 'r', encoding='utf-8')
        assert result == valid_config_data

    def test_load_yaml_config_file_not_found(self):
        """Test _load_yaml_config raises FileNotFoundError."""
        mock_file_path = pathlib.Path("/path/does/not/exist.yaml")
        with patch("core.config.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                core.config._load_yaml_config(mock_file_path)

    def test_load_yaml_config_yaml_error(self):
        """Test _load_yaml_config handles YAML parsing errors."""
        invalid_yaml_content = "invalid: [unclosed list"
        mock_file_path = pathlib.Path("/fake/path/bad_config.yaml")

        with patch("builtins.open", mock_open(read_data=invalid_yaml_content)):
            with patch("core.config.Path.exists", return_value=True):
                with pytest.raises(ValueError) as exc_info:
                    core.config._load_yaml_config(mock_file_path)
                actual_error_msg = str(exc_info.value)
                assert str(mock_file_path) in actual_error_msg
                assert "解析 YAML 文件" in actual_error_msg
                assert "while parsing a flow sequence" in actual_error_msg

    def test_load_yaml_config_io_error(self):
        """Test _load_yaml_config handles general IO errors."""
        mock_file_path = pathlib.Path("/fake/path/io_error.yaml")
        with patch("core.config.Path.exists", return_value=True):
            with patch("builtins.open", mock_open()) as mock_file:
                mock_file.side_effect = IOError("Permission denied")
                with pytest.raises(RuntimeError) as exc_info:
                    core.config._load_yaml_config(mock_file_path)
            actual_error_msg = str(exc_info.value)
            assert str(mock_file_path) in actual_error_msg
            assert "读取配置文件" in actual_error_msg
            assert "Permission denied" in actual_error_msg


# --- Tests for main loading functions (load_settings, setup_logging) ---

class TestLoadSettings:

    def test_load_settings_initial_load(self, valid_config_data, monkeypatch):
        """Test load_settings loads config correctly on first call."""
        # Ensure _settings is initially None or reset
        monkeypatch.setattr("core.config._settings", None)
        yaml_content = yaml.dump(valid_config_data)

        with patch("builtins.open", mock_open(read_data=yaml_content)) as mock_file:
            with patch("core.config.Path.exists", return_value=True):
                # Call the function
                loaded_settings = core.config.load_settings()

        # Assert the returned data is correct
        assert loaded_settings == valid_config_data
        # Assert the internal cache is updated
        assert core.config._settings == valid_config_data
        # Assert file was opened
        mock_file.assert_called()

    def test_load_settings_cached(self, valid_config_data, monkeypatch):
        """Test load_settings returns cached data on subsequent calls."""
        # Pre-populate the cache
        monkeypatch.setattr("core.config._settings", valid_config_data)
        # Mock _load_yaml_config to verify it's NOT called again
        mock_load_yaml = MagicMock(return_value={"should": "not be used"})
        monkeypatch.setattr("core.config._load_yaml_config", mock_load_yaml)

        # Call the function
        loaded_settings = core.config.load_settings()

        # Assert the returned data is from the cache
        assert loaded_settings == valid_config_data
        # Assert _load_yaml_config was NOT called
        mock_load_yaml.assert_not_called()


class TestSetupLogging:

    def test_setup_logging_already_initialized(self, monkeypatch):
        """Test setup_logging does nothing if already initialized."""
        monkeypatch.setattr(
            "core.config._logger_initialized", True)  # Set flag

        # Mock _load_yaml_config to verify it's NOT called
        mock_load_yaml = MagicMock(return_value={})
        monkeypatch.setattr("core.config._load_yaml_config", mock_load_yaml)
        with patch("logging.config.dictConfig") as mock_dict_config:
            # Call the function
            core.config.setup_logging()

        # Assert neither loading nor configuring happened
        mock_load_yaml.assert_not_called()
        mock_dict_config.assert_not_called()

# --- Tests for utility functions (get_config_value, get_settings) ---


class TestGetConfigValue:

    # Automatically run for all tests in this class
    @pytest.fixture(autouse=True)
    def ensure_valid_settings(self, valid_config_data, monkeypatch):
        """Ensure a known config is loaded before each test."""
        monkeypatch.setattr("core.config._settings", valid_config_data)

    def test_get_config_value_existing_simple_key(self):
        """Test retrieving a top-level value."""
        value = core.config.get_config_value('app.name')
        assert value == 'TestApp'

    def test_get_config_value_existing_nested_key(self):
        """Test retrieving a nested value."""
        value = core.config.get_config_value('model_defaults.temperature')
        assert value == 0.5

    def test_get_config_value_nonexistent_key_with_default(self):
        """Test retrieving a non-existent key with a default."""
        default_val = "default_string"
        value = core.config.get_config_value(
            'non.existent.key', default=default_val)
        assert value == default_val

    def test_get_config_value_nonexistent_key_no_default(self):
        """Test retrieving a non-existent key without a default."""
        value = core.config.get_config_value('another.missing.key')
        assert value is None  # Default default is None

    def test_get_config_value_missing_intermediate_key(self):
        """Test retrieving a value with a missing intermediate key."""
        value = core.config.get_config_value(
            'missing_section.some_key', default="fallback")
        assert value == "fallback"


class TestGetSettings:

    def test_get_settings_returns_loaded_config(self, valid_config_data, monkeypatch):
        """Test get_settings returns the loaded configuration."""
        monkeypatch.setattr("core.config._settings", valid_config_data)
        settings = core.config.get_settings()
        assert settings == valid_config_data
        # Test alias
        assert core.config.settings == core.config.get_settings

# --- Tests for Initialization Logic (Implicit via import) ---

# Testing the `try...except` block that runs on import is tricky and usually
# not done directly in unit tests of the module itself.
# It's more of an integration/system test.
# However, we can test the behavior if config loading fails.

# --- Helper to simulate import error scenario ---


def test_init_logic_config_failure(monkeypatch):
    """Simulates and tests the failure path during initial config load."""
    # Save original functions
    original_load_settings = core.config.load_settings
    original_setup_logging = core.config.setup_logging

    # Mock load_settings to raise RuntimeError
    def mock_load_settings_fail():
        raise RuntimeError("Import-time config load error")

    # Mock setup_logging to do nothing
    def mock_setup_logging_pass():
        pass

    # Apply mocks
    monkeypatch.setattr(core.config, 'load_settings', mock_load_settings_fail)
    monkeypatch.setattr(core.config, 'setup_logging', mock_setup_logging_pass)

    # Mock sys.exit
    mock_exit = MagicMock()
    monkeypatch.setattr('sys.exit', mock_exit)

    # Mock c_print to capture output
    mock_cprint = MagicMock()
    monkeypatch.setattr('core.config.c_print', mock_cprint)

    try:
        # This mimics the top-level execution
        core.config.load_settings()  # This will now raise our mocked error
        core.config.setup_logging()  # This shouldn't be reached
    except RuntimeError as e:
        # This block *should* be executed
        core.config.c_print(
            f"🚨 应用初始化失败: {e}", core.config.Fore.RED, prefix="💥 ")
        core.config.sys.exit(1)  # This should be called

    # Assert c_print was called with the error
    mock_cprint.assert_called_once()  # Check it was called
    args, kwargs = mock_cprint.call_args
    assert "🚨 应用初始化失败:" in args[0]
    # Our mocked error message
    assert "Import-time config load error" in args[0]
    assert args[1] == core.config.Fore.RED
    assert kwargs.get('prefix') == "💥 "

    # Assert sys.exit was called with 1
    mock_exit.assert_called_once_with(1)

    # Restore original functions (good practice in case other tests rely on them)
    monkeypatch.setattr(core.config, 'load_settings', original_load_settings)
    monkeypatch.setattr(core.config, 'setup_logging', original_setup_logging)
    # Note: sys.exit and c_print mocks are reverted by monkeypatch automatically after this function


def test_colorama_available():
    """测试 colorama 可用时的行为"""
    # 确保 colorama 能正常导入（不 mock）
    try:
        import colorama
        has_colorama = True
    except ImportError:
        has_colorama = False

    if not has_colorama:
        # 跳过此测试（或可选择安装 colorama）
        import pytest
        pytest.skip("colorama not installed")

    # 重新导入 config 模块（需清理缓存）
    if 'core.config' in sys.modules:
        del sys.modules['core.config']

    from core.config import USE_COLOR, Fore, Style
    assert USE_COLOR is True
    assert hasattr(Fore, 'RED')
    assert hasattr(Style, 'RESET_ALL')


def test_colorama_not_available():
    """测试 colorama 不可用时回退到 DummyStyle"""
    # 模拟 ImportError
    with mock.patch.dict('sys.modules', {'colorama': None}):
        # 清除已加载的模块（关键！）
        if 'core.config' in sys.modules:
            del sys.modules['core.config']

        from core.config import USE_COLOR, Fore, Style

        assert USE_COLOR is False
        assert isinstance(Fore, type(Style))  # 都是 DummyStyle 实例
        assert Fore.RED == ""
        assert Style.RESET_ALL == ""
        assert Fore.ANYTHING == ""


def _reload_config():
    """辅助函数：重载 config 模块以应用 mock 环境"""
    if 'core.config' in sys.modules:
        del sys.modules['core.config']
    from core.config import c_print
    return c_print


def test_c_print_else_branch_no_color_support():
    """测试 USE_COLOR=False 时走 else 分支"""
    with mock.patch.dict('sys.modules', {'colorama': None}):
        c_print = _reload_config()

        f = io.StringIO()
        with redirect_stdout(f):
            c_print("hello", color="RED", prefix="[INFO] ")

        assert f.getvalue() == "[INFO] hello\n"


def test_c_print_else_branch_empty_color():
    """测试 USE_COLOR=True 但 color='' 时走 else 分支"""
    # 确保 colorama 可用
    try:
        import colorama
        has_colorama = True
    except ImportError:
        has_colorama = False

    if not has_colorama:
        import pytest
        pytest.skip("colorama not installed")

    c_print = _reload_config()

    f = io.StringIO()
    with redirect_stdout(f):
        c_print("hello", color="", prefix="[DEBUG] ")

    assert f.getvalue() == "[DEBUG] hello\n"


def test_c_print_else_branch_no_color_arg():
    """测试不传 color 参数（默认空字符串）"""
    # 无论 USE_COLOR 是否为 True，只要 color 为空就走 else
    c_print = _reload_config()

    f = io.StringIO()
    with redirect_stdout(f):
        c_print("hello", prefix="[LOG] ")  # color 默认为 ""

    assert f.getvalue() == "[LOG] hello\n"


# 确保能导入 load_settings
if 'core.config' in sys.modules:
    del sys.modules['core.config']  # 清理缓存，避免 _settings 已加载


@pytest.mark.parametrize("exc", [
    FileNotFoundError("config.yaml not found"),
    ValueError("Invalid YAML syntax"),
    RuntimeError("Decryption failed")
])
def test_load_settings_handles_exceptions(exc):
    # 1. 确保模块未被缓存
    if 'core.config' in sys.modules:
        del sys.modules['core.config']

    # 2. 动态导入
    from core.config import load_settings, _settings

    # 3. 显式重置（虽然刚导入应为 None，但保险起见）
    import core.config
    core.config._settings = None

    # 4. Mock _load_yaml_config 抛出异常
    with mock.patch('core.config._load_yaml_config', side_effect=exc):
        f = StringIO()
        with redirect_stdout(f):
            with pytest.raises(RuntimeError, match=f"配置加载失败: {exc}"):
                load_settings()

        # 验证错误输出
        output = f.getvalue()
        assert "❌ 致命错误: 无法加载主配置文件" in output
        assert "🚨 " in output

# 清理 logging 状态的 fixture


@pytest.fixture(autouse=True)
def reset_logging():
    """每个测试前后重置 logging 状态"""
    # 清除所有已存在的 handler 和 logger
    logging.shutdown()
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)
    # 重置 logging 模块内部状态
    logging.Logger.manager.loggerDict.clear()
    yield
    # 再次清理（保险）
    logging.shutdown()
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)
    logging.Logger.manager.loggerDict.clear()


def _reload_config_module():
    """强制重载 config 模块以重置 _logger_initialized"""
    if 'core.config' in sys.modules:
        del sys.modules['core.config']
    from core.config import setup_logging, _logger_initialized
    return setup_logging, _logger_initialized


def test_setup_logging_success():
    # 禁用 colorama，避免 ANSI 码干扰
    with mock.patch.dict('sys.modules', {'colorama': None}):
        if 'core.config' in sys.modules:
            del sys.modules['core.config']
        from core.config import setup_logging

        mock_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"standard": {"format": "%(message)s"}},
            "handlers": {"console": {"class": "logging.StreamHandler", "level": "INFO"}},
            "root": {"level": "INFO", "handlers": ["console"]}
        }

        # 👇 关键：直接 mock LOGGING_CONFIG_FILE_PATH
        fake_log_config_path = Path("/fake/project/config/logging_config.yaml")

        f = StringIO()
        with mock.patch('core.config._load_yaml_config', return_value=mock_config):
            with mock.patch('core.config.LOGGING_CONFIG_FILE_PATH', fake_log_config_path):
                with mock.patch.object(Path, 'mkdir'):  # 防止 mkdir 报错
                    with redirect_stdout(f):
                        setup_logging()

        # 现在输出路径就是 fake 路径，且无颜色码
        assert f.getvalue().strip(
        ) == f"✅ 日志系统初始化成功 (配置文件: {fake_log_config_path})"


def test_setup_logging_failure_fallback(caplog):
    """测试 logging 配置加载失败，回退到 basicConfig（except 分支）"""
    # 禁用 colorama，避免 ANSI 干扰 c_print 输出
    with mock.patch.dict('sys.modules', {'colorama': None}):
        if 'core.config' in sys.modules:
            del sys.modules['core.config']
        from core.config import setup_logging, _logger_initialized

        exception = FileNotFoundError("logging_config.yaml not found")

        f = StringIO()
        fake_log_path = Path("/fake/project/config/logging_config.yaml")
        with mock.patch('core.config._load_yaml_config', side_effect=exception):
            with mock.patch('core.config.LOGGING_CONFIG_FILE_PATH', fake_log_path):  # 👈 更可靠
                with redirect_stdout(f):
                    setup_logging()

        # 验证 c_print 警告输出（标准输出）
        output = f.getvalue()
        assert "⚠️ 警告: 无法加载 logging 配置" in output
        assert "将使用默认 logging 设置" in output

        # 验证已回退到 basicConfig：root logger 有 handler
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0
        assert any(isinstance(h, logging.StreamHandler)
                   for h in root_logger.handlers)

        # 验证 _logger_initialized 保持 False
        assert _logger_initialized is False

        # ✅ 使用 caplog 验证日志消息被记录（无需捕获 stderr！）
        with caplog.at_level(logging.WARNING):
            test_logger = logging.getLogger("test.fallback")
            test_logger.warning("test fallback log")

        assert "test fallback log" in caplog.text
        assert "Logging 配置加载失败，使用基础配置" in caplog.text


def test_get_logger_when_logging_initialized():
    """
    测试当 logging 已初始化时，get_logger 正常工作。
    """
    from core.config import get_logger
    with mock.patch('core.config._logger_initialized', True):
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"


def test_get_logger_when_logging_not_initialized():
    """
    测试当 logging 未初始化时，get_logger 不崩溃、不自动初始化。
    """
    from core.config import get_logger
    with mock.patch('core.config._logger_initialized', False):
        logger = get_logger("test.uninit")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.uninit"
        assert len(logger.handlers) == 0


def test_get_logger_without_setup_logging():
    """
    真实场景：从未调用 setup_logging，直接调用 get_logger。
    """
    if 'core.config' in sys.modules:
        del sys.modules['core.config']
    from core.config import get_logger, _logger_initialized

    assert _logger_initialized is False
    logger = get_logger("my.app")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "my.app"
    assert _logger_initialized is False
    logger.info("This is a test")


class TestGetSettings:
    """Test get_settings() in core/config.py"""

    def test_returns_full_settings_dict(self):
        """get_settings() should return a properly structured settings dictionary."""
        from core.config import get_settings
        
        settings = get_settings()
        
        # 检验返回值的格式和结构
        assert isinstance(settings, dict)
        
        # 检验主要配置节存在
        expected_sections = ["app", "cli", "database", "model_defaults", "models", "services", "user_preferences", "web"]
        for section in expected_sections:
            assert section in settings, f"Missing section: {section}"
        
        # 检验 app 配置节的结构
        assert isinstance(settings["app"], dict)
        assert "debug" in settings["app"]
        assert "name" in settings["app"]
        assert "version" in settings["app"]
        assert isinstance(settings["app"]["debug"], bool)
        assert isinstance(settings["app"]["name"], str)
        assert isinstance(settings["app"]["version"], str)
        
        # 检验嵌套结构存在
        assert isinstance(settings["models"], dict)
        assert isinstance(settings["user_preferences"], dict)
        assert isinstance(settings["model_defaults"], dict)
        
        # 检验关键字段存在且类型正确
        assert isinstance(settings["cli"]["default_mode"], str)
        assert isinstance(settings["database"]["chat_history_path"], str)


def test_initialize_app_success():
    """
    测试 initialize_app 在 load_settings 和 setup_logging 成功时正常执行。
    """
    from core.config import initialize_app
    with mock.patch('core.config.load_settings') as mock_load, \
            mock.patch('core.config.setup_logging') as mock_setup:
        initialize_app()
        mock_load.assert_called_once()
        mock_setup.assert_called_once()


def test_initialize_app_load_settings_failure():
    """
    测试 initialize_app 在 load_settings 抛出 RuntimeError 时正确处理并重新抛出。
    """
    from core.config import initialize_app
    with mock.patch('core.config.load_settings', side_effect=RuntimeError("Settings invalid")), \
            mock.patch('core.config.setup_logging') as mock_setup, \
            mock.patch('core.config.c_print') as mock_cprint:
        with pytest.raises(RuntimeError, match="Settings invalid"):
            initialize_app()
        mock_cprint.assert_called_once()
        args, kwargs = mock_cprint.call_args
        assert "🚨 应用初始化失败" in args[0]
        assert kwargs.get("prefix") == "💥 "
        mock_setup.assert_not_called()


def test_initialize_app_setup_logging_failure():
    """
    测试 initialize_app 在 setup_logging 抛出 RuntimeError 时正确处理并重新抛出。
    """
    from core.config import initialize_app
    with mock.patch('core.config.load_settings') as mock_load, \
            mock.patch('core.config.setup_logging', side_effect=RuntimeError("Logging config broken")), \
            mock.patch('core.config.c_print') as mock_cprint:
        with pytest.raises(RuntimeError, match="Logging config broken"):
            initialize_app()
        mock_cprint.assert_called_once()
        assert "🚨 应用初始化失败" in mock_cprint.call_args[0][0]
        mock_load.assert_called_once()
