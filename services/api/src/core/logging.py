import logging
import socket
import sys

import structlog


class ConsoleOnlyRenderer:
    """Renders readable output to console, preserves dict for JSON"""

    def __call__(self, logger, method_name, event_dict):
        timestamp = event_dict.get('timestamp', '')
        level = event_dict.get('level', 'info').upper()
        event = event_dict.get('event', '')

        context_parts = []
        for key, value in event_dict.items():
            if key not in ['timestamp', 'level', 'event']:
                context_parts.append(f"{key}={value}")

        context_str = " ".join(context_parts) if context_parts else ""
        console_msg = f"{timestamp} [{level:5}] {event:35} {context_str}"

        print(console_msg, file=sys.stdout, flush=True)

        return event_dict


def setup_logging(
    log_level: str = "INFO",
) -> structlog.BoundLogger:
    from core.config import settings

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

            logging.basicConfig(
                format="%(message)s",
                level=getattr(logging, log_level.upper()),
                handlers=[loki_handler],
                force=True,
            )
        except Exception as e:
            print(f"Warning: Failed to initialize Loki handler: {e}")
            logging.basicConfig(
                format="%(message)s",
                level=getattr(logging, log_level.upper()),
                handlers=[logging.StreamHandler(sys.stdout)],
                force=True,
            )
    else:
        logging.basicConfig(
            format="%(message)s",
            level=getattr(logging, log_level.upper()),
            handlers=[logging.StreamHandler(sys.stdout)],
            force=True,
        )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", key="timestamp"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        ConsoleOnlyRenderer(),
        structlog.processors.JSONRenderer(sort_keys=False),
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
