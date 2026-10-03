"""
JARVIS Logger — Centralized structured logging
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Lazy import config to avoid circular deps
def _get_logs_dir():
    try:
        from core.config import LOGS_DIR
        return LOGS_DIR
    except Exception:
        return Path("data/logs")


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("JARVIS")
    logger.setLevel(logging.DEBUG)

    # Console handler with rich formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        "\033[36m[%(asctime)s]\033[0m \033[33m[JARVIS]\033[0m %(levelname)s: %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    # File handler
    try:
        logs_dir = _get_logs_dir()
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / f"jarvis_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_fmt = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not set up file logging: {e}")

    return logger


log = _setup_logger()
