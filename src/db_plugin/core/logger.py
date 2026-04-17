"""Centralized logging setup for the DB plugin."""

import logging
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[3] / "logs"
LOG_DIR.mkdir(exist_ok=True)


def setup_logger(
    name: str = "db_plugin",
    level: int = logging.DEBUG,
    log_file: str = "app.log",
) -> logging.Logger:
    """Create and configure a logger with file + console handlers."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-5s] %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # File handler — rotating, 5 MB max per file, keep 3 backups
    from logging.handlers import RotatingFileHandler

    file_handler = RotatingFileHandler(
        LOG_DIR / log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()
