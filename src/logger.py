"""
Module: src/logger.py
Purpose: Configure structured console and rotating-file logging for ScrapeSignal
Author: ScrapeSignal Team
Created: 2026-05-10

Dependencies:
    - src.config.py (settings)

Used by:
    - src.main (orchestrator startup)
    - All modules via standard logging.getLogger(__name__)
"""

# Standard library
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, cast

# Third-party
from pythonjsonlogger import jsonlogger

# Local
from src.config import settings

TEXT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
JSON_LOG_FORMAT = (
    "%(asctime)s %(name)s %(levelname)s %(message)s %(module)s %(funcName)s %(lineno)d"
)


def _build_formatter() -> logging.Formatter:
    """Build the configured log formatter.

    Returns:
        Text or JSON formatter based on `settings.LOG_FORMAT`.
    """
    if settings.LOG_FORMAT == "json":
        formatter = jsonlogger.JsonFormatter(JSON_LOG_FORMAT)  # type: ignore[no-untyped-call]
        return cast(logging.Formatter, formatter)
    return logging.Formatter(TEXT_LOG_FORMAT)


def _build_console_handler(formatter: logging.Formatter) -> logging.StreamHandler[Any]:
    """Build console logging handler.

    Args:
        formatter: Formatter to apply to console logs.

    Returns:
        Configured stream handler.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(settings.LOG_LEVEL)
    return handler


def _build_file_handler(formatter: logging.Formatter) -> RotatingFileHandler:
    """Build rotating file logging handler.

    Args:
        formatter: Formatter to apply to file logs.

    Returns:
        Configured rotating file handler.
    """
    log_path = Path(settings.LOG_FILE_PATH)
    if log_path.parent != Path():
        log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=settings.LOG_FILE_MAX_BYTES,
        backupCount=settings.LOG_FILE_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(formatter)
    handler.setLevel(settings.LOG_LEVEL)
    return handler


def setup_logging() -> None:
    """Configure root logging for the ScrapeSignal process.

    Existing handlers are replaced so repeated test imports do not duplicate
    log lines.
    """
    formatter = _build_formatter()
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(settings.LOG_LEVEL)
    root_logger.addHandler(_build_console_handler(formatter))
    root_logger.addHandler(_build_file_handler(formatter))

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    root_logger.info(
        "ScrapeSignal logging configured",
        extra=_safe_logging_context(),
    )


def _safe_logging_context() -> dict[str, Any]:
    """Return non-sensitive logging context.

    Returns:
        Dictionary containing safe runtime metadata.
    """
    return {
        "environment": settings.ENVIRONMENT,
        "dry_run": settings.DRY_RUN,
        "log_format": settings.LOG_FORMAT,
    }
