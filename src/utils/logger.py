"""Logging configuration using structlog."""

import logging
import sys
from typing import Optional

import structlog
from structlog.types import EventDict, Processor

from .config import settings


def add_log_level(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add log level to event dict."""
    if method_name == "warn":
        method_name = "warning"
    event_dict["level"] = method_name.upper()
    return event_dict


def setup_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Setup and configure structured logging.

    Args:
        name: Logger name (optional)

    Returns:
        Configured structlog logger
    """
    log_level = getattr(logging, settings.log_level.upper())

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Configure structlog
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        add_log_level,
    ]

    if settings.environment == "development":
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger(name)


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a logger instance.

    Args:
        name: Logger name (optional)

    Returns:
        Structlog logger instance
    """
    return structlog.get_logger(name)
