"""Centralized logging configuration for the trading bot."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure root logger with console and optional file handlers.

    Args:
        log_file: Path to log file. Defaults to logs/trading_bot.log under project root.
        level: Logging level (default INFO).

    Returns:
        Configured logger instance for the trading bot.
    """
    if log_file is None:
        project_root = Path(__file__).resolve().parent.parent
        log_dir = project_root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = str(log_dir / "trading_bot.log")

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger("trading_bot")
    root_logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging is called more than once
    if root_logger.handlers:
        return root_logger

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    return root_logger
