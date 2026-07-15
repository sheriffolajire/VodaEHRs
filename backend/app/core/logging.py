"""Logging configuration separated by concern.

Log streams: application, audit, security. Docker logs are handled
by the infrastructure layer.
"""

import logging
import sys
from pathlib import Path

LOG_DIR = Path("logs")
_STREAMS = ("application", "audit", "security")


def configure_logging() -> None:
    """Configure root and named loggers with console and file handlers."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(logging.INFO)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    for stream in _STREAMS:
        logger = logging.getLogger(stream)
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(LOG_DIR / f"{stream}.log", encoding="utf-8")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a named logger ('application', 'audit', 'security')."""
    return logging.getLogger(name)
