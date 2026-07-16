import logging
import sys

import structlog
from structlog.types import Processor

from app.core.config import settings

logger = structlog.get_logger("app.exception")

def setup_logging() -> None:
    """
    Setting up Structlog for structured logging
    In production/staging, produces formated JSON inline.
    In development, produces pretty-printed output
    """
    # 1. Setting Python logging for redirect to default output
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    )

    # 2. Shared processors for structlog
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.ENVIRONMENT in ("production", "staging"):
        processors = shared_processors + [structlog.processors.JSONRenderer()]
    else:
        processors = shared_processors + [structlog.dev.ConsoleRenderer(colors=True)]

    structlog.configure(
        processors = processors,
        logger_factory = structlog.stdlib.LoggerFactory(),
        wrapper_class = structlog.stdlib.BoundLogger,
        cache_logger_on_first_use = True,
    )
