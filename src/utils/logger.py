"""Structured logging setup with daily rotating log files."""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

from src.utils.config import get_logs_dir

console = Console()

_logger: logging.Logger | None = None


def get_logger(name: str = "realestate") -> logging.Logger:
    """Get or create the application logger with console + file handlers."""
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Console handler with rich formatting
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
    )
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    # File handler with daily rotation
    log_dir = get_logs_dir()
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    _logger = logger
    return logger
