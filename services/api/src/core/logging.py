import logging
import sys
from typing import Any

import structlog
from fluent import sender


class FluentdLogger:
    def __init__(self, host: str = "localhost", port: int = 24224, tag: str = "api-scheduler"):
        self.logger = sender.FluentSender(tag, host=host, port=port)

    def emit(self, level: str, message: str, **kwargs: Any) -> None:
        try:
            self.logger.emit(level, {
                "message": message,
                "level": level,
                **kwargs
            })
        except Exception:
            pass

    def info(self, message: str, **kwargs: Any) -> None:
        self.emit("info", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self.emit("warning", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self.emit("error", message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        self.emit("debug", message, **kwargs)

    def close(self) -> None:
        if self.logger:
            self.logger.close()


class FluentdProcessor:
    def __init__(self, fluentd_logger: FluentdLogger):
        self.fluentd_logger = fluentd_logger

    def __call__(self, logger, method_name, event_dict):
        level = event_dict.get("level", "info").lower()
        message = event_dict.pop("event", "")

        try:
            self.fluentd_logger.emit(level, message, **event_dict)
        except Exception:
            pass

        return event_dict


def setup_logging(
    fluentd_host: str = "localhost",
    fluentd_port: int = 24224,
    log_level: str = "INFO",
    enable_fluentd: bool = True,
) -> structlog.BoundLogger:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
    ]

    if enable_fluentd:
        fluentd_logger = FluentdLogger(host=fluentd_host, port=fluentd_port)
        processors.append(FluentdProcessor(fluentd_logger))
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )

    return structlog.get_logger()


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
