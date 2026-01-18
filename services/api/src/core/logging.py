import logging
import socket
import sys

import structlog


def setup_logging(
    log_level: str = "INFO",
) -> structlog.BoundLogger:
    from core.config import settings

    handlers = []

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    handlers.append(console_handler)

    if settings.loki_url:
        try:
            from logging_loki import LokiHandler

            loki_handler = LokiHandler(
                url=f"{settings.loki_url}/loki/api/v1/push",
                tags={
                    "application": settings.otel_service_name,
                    "environment": "development" if settings.dev else "production",
                    "host": socket.gethostname(),
                },
                version="1",
            )
            loki_handler.setLevel(getattr(logging, log_level.upper()))
            handlers.append(loki_handler)
        except Exception as e:
            print(f"Warning: Failed to initialize Loki handler: {e}")

    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
        handlers=handlers,
        force=True,
    )

    if settings.dev:
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.dev.ConsoleRenderer(),
        ]
    else:
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )

    logger = structlog.get_logger()
    if settings.loki_url:
        logger.info(
            "logging_initialized",
            log_level=log_level,
            loki_enabled=True,
            loki_url=settings.loki_url,
        )
    else:
        logger.info(
            "logging_initialized",
            log_level=log_level,
            loki_enabled=False,
        )

    return logger


def get_logger() -> structlog.BoundLogger:
    import inspect

    frame = inspect.currentframe()
    caller_frame = frame.f_back if frame else None

    logger = structlog.get_logger()

    if caller_frame:
        file_name = caller_frame.f_code.co_filename.split("/")[-1]
        line_number = caller_frame.f_lineno
        function_name = caller_frame.f_code.co_name

        logger = logger.bind(
            file=file_name,
            line=line_number,
            function=function_name,
        )

    return logger
