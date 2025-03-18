"""Logging configuration for the project."""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pythonjsonlogger import jsonlogger


def setup_logging() -> None:
    """
    Configure logging based on environment.

    Raises:
        OSError: If log directory cannot be created or accessed

    """
    logger = logging.getLogger()

    # Clear any existing handlers
    logger.handlers.clear()

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    try:
        log_dir.mkdir(exist_ok=True)
    except OSError as e:
        error_msg = "Failed to create log directory: " + str(e)
        raise OSError(error_msg) from e

    # Configure handlers
    handlers: list[logging.Handler] = []

    # Console handler
    console_handler = logging.StreamHandler()
    handlers.append(console_handler)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    handlers.append(file_handler)

    # Set formatters based on environment
    if os.getenv("ENVIRONMENT") == "production":
        # Production logging with JSON format
        json_formatter: jsonlogger.JsonFormatter = jsonlogger.JsonFormatter(  # type: ignore[no-untyped-call]
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(json_formatter)
        file_handler.setFormatter(json_formatter)
        logger.setLevel(logging.INFO)
    else:
        # Development logging with human-readable format
        dev_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(dev_formatter)
        file_handler.setFormatter(dev_formatter)
        logger.setLevel(logging.DEBUG)

    # Add handlers to logger
    for handler in handlers:
        logger.addHandler(handler)

    logger.propagate = False

    # Set specific log levels for third-party libraries
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("django").setLevel(logging.INFO)
    logging.getLogger("aiogram").setLevel(logging.INFO)

    # Log startup message
    logger.info("Logging system initialized")
