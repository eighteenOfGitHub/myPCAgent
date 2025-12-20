# tests/test_logger.py
"""
Tests for the core.logger module.
"""

import logging
import pytest
from unittest.mock import patch, MagicMock
from core.logger import get_logger, getLogger, session_context
import sys
import importlib


class TestGetLogger:
    """Tests for the get_logger function."""

    def test_get_logger_default(self):
        """Test getting the root logger."""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'root'
        # Verify it's the standard library's getLogger
        assert logger is logging.getLogger(None)

    def test_get_logger_with_name(self):
        """Test getting a named logger."""
        name = "test.module"
        logger = get_logger(name)
        assert isinstance(logger, logging.Logger)
        assert logger.name == name
        assert logger is logging.getLogger(name)

    def test_getLogger_alias(self):
        """Test that getLogger alias works."""
        assert getLogger is get_logger


class TestSessionContext:
    """Tests for the session_context manager."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, monkeypatch):
        """
        Setup: Mock the session context filter functions.
        Teardown: Ensure mocks are reset automatically by pytest/monkeypatch.
        """
        # Create mock functions
        self.mock_set_sid = MagicMock()
        self.mock_clear_sid = MagicMock()

        # Patch the imports within core.logger
        monkeypatch.setattr("core.logger.set_session_id", self.mock_set_sid)
        monkeypatch.setattr("core.logger.clear_session_id",
                            self.mock_clear_sid)
        # Simulate successful import of session context features
        monkeypatch.setattr("core.logger._HAS_SESSION_CONTEXT", True)

    def test_session_context_normal_flow(self):
        """Test normal entry and exit of session_context."""
        session_id = "test-session-id-123"

        with session_context(session_id):
            # Inside the context, set should have been called
            self.mock_set_sid.assert_called_once_with(session_id)
            self.mock_clear_sid.assert_not_called()

        # After exiting, clear should have been called
        self.mock_set_sid.assert_called_once()  # Still only once
        self.mock_clear_sid.assert_called_once()

    def test_session_context_exception_handling(self):
        """Test that session_id is cleared even if an exception occurs."""
        session_id = "test-session-id-except"
        expected_exception = ValueError("An error inside the context!")

        with pytest.raises(ValueError) as exc_info:
            with session_context(session_id):
                self.mock_set_sid.assert_called_once_with(session_id)
                self.mock_clear_sid.assert_not_called()
                raise expected_exception

        # Assert the exception is the one we raised
        assert exc_info.value is expected_exception

        # Assert that clear was still called despite the exception
        self.mock_set_sid.assert_called_once()
        self.mock_clear_sid.assert_called_once()

    def test_session_context_disabled(self, monkeypatch):
        """Test session_context when session context features are disabled."""
        # Simulate the case where session_context_filter is NOT available
        monkeypatch.setattr("core.logger._HAS_SESSION_CONTEXT", False)

        # Mock dummy functions to check they are not called
        dummy_set = MagicMock()
        dummy_clear = MagicMock()
        monkeypatch.setattr("core.logger.set_session_id", dummy_set)
        monkeypatch.setattr("core.logger.clear_session_id", dummy_clear)

        session_id = "should-not-be-used"

        # Using session_context should not call the dummy setters/clearers
        with session_context(session_id):
            dummy_set.assert_not_called()
            dummy_clear.assert_not_called()

        # Exiting should also not call them
        dummy_set.assert_not_called()
        dummy_clear.assert_not_called()
        # The block should execute normally without errors
        assert True  # Implicitly passes if no exception was raised


# --- Integration/Smoke Test for Actual Logging (Optional but useful) ---
# This part verifies that the logger obtained actually uses the configuration
# defined in logging_config.yaml. It doesn't achieve 100% line coverage of
# logger.py itself, but tests its integration with the config.

class TestLoggerIntegration:
    """Integration tests for logger with actual configuration."""

    @pytest.fixture(scope="class")  # Run once per test class
    def temp_log_file(self, tmpdir_factory):
        """Provide a temporary log file path for testing."""
        # Use tmpdir_factory for session-scoped fixture compatibility if needed later
        tmp_dir = tmpdir_factory.mktemp("logs")
        log_file = tmp_dir.join("test_integration.log")
        return str(log_file)

    def test_logger_uses_configured_formatter_and_level(self, temp_log_file, caplog):
        """
        Smoke test: Check if logger respects configuration for level and formatting.
        Note: This assumes the config sets up handlers correctly.
        We'll use caplog to capture log messages instead of writing to a real file
        for simplicity in this unit test context.
        """
        # Import here to ensure config is loaded if not done globally
        # Although core/config.py likely loads it on import
        import core.config  # Ensure setup_logging is called

        # Get a logger that should be configured
        logger_name = "test.integration.smoke"
        logger = get_logger(logger_name)

        # Set caplog to capture at least INFO level
        with caplog.at_level(logging.INFO, logger=logger_name):
            test_msg_debug = "This is a DEBUG message"
            test_msg_info = "This is an INFO message"
            logger.debug(test_msg_debug)
            logger.info(test_msg_info)

        # Assertions using caplog
        # Debug message might not appear depending on config, but INFO should
        # Find the INFO record
        info_records = [record for record in caplog.records if record.levelname ==
                        'INFO' and record.message == test_msg_info]
        assert len(info_records) == 1
        info_record = info_records[0]

        # Check if the message format matches one defined in logging_config.yaml
        # E.g., simple format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        # This is a bit fragile but checks integration
        log_output_line = caplog.text  # Gets the formatted string output
        assert test_msg_info in log_output_line
        # Basic check for presence of expected parts of the format
        assert info_record.name in log_output_line  # logger name
        assert info_record.levelname in log_output_line  # level
        # Note: Checking exact asctime format is tricky with caplog.text,
        # but checking its presence conceptually works.
        # A more robust way would be to configure a specific handler for testing.

    # Note: Testing actual file output would require parsing the log file
    # and is more complex. caplog is generally preferred for unit tests.
    # If you must test file output, consider setting up a specific test handler
    # or temporarily modifying the logging config for the test.


@pytest.fixture
def reset_core_logger():
    import core.logger
    importlib.reload(core.logger)
    yield core.logger


@pytest.fixture
def force_import_error_on_session_filter(monkeypatch):
    original_module = sys.modules.get('app.logging.session_context_filter')
    if original_module:
        monkeypatch.delitem(sys.modules, 'app.logging.session_context_filter')

    with patch.dict('sys.modules', {'app.logging.session_context_filter': None}):
        import core.logger
        importlib.reload(core.logger)
        yield core.logger


def test_session_context_available(reset_core_logger):
    """
    测试当 app.logging.session_context_filter 模块存在且可导入时，
    _HAS_SESSION_CONTEXT 为 True，set_session_id 和 clear_session_id
    指向导入的函数，并且 session_context 上下文管理器能正确调用它们。
    """
    logger_module = reset_core_logger

    # 1. 验证模块导入成功状态
    assert logger_module._HAS_SESSION_CONTEXT == True, f"Expected _HAS_SESSION_CONTEXT=True, got {logger_module._HAS_SESSION_CONTEXT}. Check if app/logging/session_context_filter.py exists and is importable."

    # 2. 验证 set/clear 函数指向正确的模块 (间接证明不是 dummy)
    # 注意：直接比较函数对象可能因 reload 而失败，比较 __module__ 更稳健
    assert hasattr(logger_module.set_session_id,
                   '__module__'), "set_session_id should be a function with a __module__ attribute."
    assert logger_module.set_session_id.__module__ == 'app.logging.session_context_filter', f"set_session_id.__module__ expected 'app.logging.session_context_filter', got '{logger_module.set_session_id.__module__}'"

    assert hasattr(logger_module.clear_session_id,
                   '__module__'), "clear_session_id should be a function with a __module__ attribute."
    assert logger_module.clear_session_id.__module__ == 'app.logging.session_context_filter', f"clear_session_id.__module__ expected 'app.logging.session_context_filter', got '{logger_module.clear_session_id.__module__}'"

    test_sid = "test_session_123"
    with patch.object(logger_module, 'set_session_id') as mock_set, \
            patch.object(logger_module, 'clear_session_id') as mock_clear:

        with logger_module.session_context(test_sid):
            pass  # 模拟在上下文中的操作

        mock_set.assert_called_once_with(test_sid)
        mock_clear.assert_called_once()


def test_session_context_not_available(force_import_error_on_session_filter):
    """
    测试当 app.logging.session_context_filter 模块不存在导致 ImportError 时，
    _HAS_SESSION_CONTEXT 为 False，set_session_id 和 clear_session_id
    被替换为不执行任何操作的 dummy 函数，并且 session_context 上下文管理器
    能够无错误地使用这些 dummy 函数。
    """
    logger_module = force_import_error_on_session_filter

    assert logger_module._HAS_SESSION_CONTEXT == False
    assert callable(logger_module.set_session_id)
    assert callable(logger_module.clear_session_id)

    try:
        logger_module.set_session_id("test_sid_for_dummy")
        logger_module.clear_session_id()
    except Exception as e:
        pytest.fail(f"Dummy functions raised an exception: {e}")
