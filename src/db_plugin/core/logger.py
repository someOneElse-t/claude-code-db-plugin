"""Centralized logging setup for the DB plugin."""

import logging
import os
import sys
from pathlib import Path

LOG_DIR = Path.home() / ".claude-code-db-plugin" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}


def get_logger(name: str = "db_plugin") -> logging.Logger:
    """Get the application-wide logger instance."""
    return logging.getLogger(name)


def setup_logger(
    name: str = "db_plugin",
    level: int | str | None = None,
    log_file: str | None = None,
) -> logging.Logger:
    """Create and configure the root logger with file + console handlers.

    Call once at application startup. Subsequent calls return the
    already-configured logger.

    Parameters
    ----------
    name : str
        Logger name (default: "db_plugin").
    level : int | str | None
        Root logging level. Falls back to ``DB_PLUGIN_LOG_LEVEL`` env var,
        then ``INFO``.
    log_file : str | None
        Log filename (default: ``DB_PLUGIN_LOG_FILE`` env var, then "app.log").
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    # Resolve level: arg > env > default
    if level is None:
        level = os.environ.get("DB_PLUGIN_LOG_LEVEL", "INFO")
    if isinstance(level, str):
        level = _LEVEL_MAP.get(level.upper(), logging.INFO)
    logger.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-5s] %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # File handler — rotating, 5 MB max per file, keep 3 backups
    from logging.handlers import RotatingFileHandler

    file_name = log_file or os.environ.get("DB_PLUGIN_LOG_FILE", "app.log")
    file_handler = RotatingFileHandler(
        LOG_DIR / file_name,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()
