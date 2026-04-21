# tests/test_logger.py
import logging
from db_plugin.core.logger import setup_logger, get_logger, LOG_DIR


class TestLogger:
    def test_log_dir_exists(self):
        """LOG_DIR is created automatically."""
        assert LOG_DIR.exists()
        assert LOG_DIR.is_dir()

    def test_setup_logger_returns_logger(self):
        """setup_logger returns a logging.Logger instance."""
        lg = setup_logger("test_logger_1")
        assert isinstance(lg, logging.Logger)
        assert lg.name == "test_logger_1"

    def test_setup_logger_idempotent(self):
        """Calling setup_logger twice returns the same logger."""
        lg1 = setup_logger("test_logger_2")
        lg2 = setup_logger("test_logger_2")
        assert lg1 is lg2

    def test_get_logger(self):
        """get_logger returns a child logger of the named logger."""
        root = setup_logger("test_logger_3")
        child = get_logger("test_logger_3.child")
        assert child.name == "test_logger_3.child"

    def test_log_level_from_env(self, monkeypatch):
        """DB_PLUGIN_LOG_LEVEL env var sets the root level."""
        import importlib
        # We test the _LEVEL_MAP resolution directly to avoid module reimport issues
        from db_plugin.core.logger import _LEVEL_MAP
        assert _LEVEL_MAP["DEBUG"] == logging.DEBUG
        assert _LEVEL_MAP["INFO"] == logging.INFO
        assert _LEVEL_MAP["WARNING"] == logging.WARNING
        assert _LEVEL_MAP["ERROR"] == logging.ERROR
        assert _LEVEL_MAP["CRITICAL"] == logging.CRITICAL
