import functools
import inspect
import time
from typing import Any, Callable, TypeVar

from core.logging import get_logger
from core.otel import get_tracer
from opentelemetry import trace

logger = get_logger()
tracer = get_tracer()

F = TypeVar("F", bound=Callable[..., Any])


def log(
    operation_name: str | None = None,
    log_args: bool = True,
    log_result: bool = False,
    log_level: str = "info",
):
    def decorator(func: F) -> F:
        func_file = func.__code__.co_filename
        func_line = func.__code__.co_firstlineno

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.perf_counter()
            span = tracer.start_span(op_name)

            log_context = {
                "function": func.__name__,
                "module": func.__module__,
                "file": func_file.split("/")[-1],
                "line": func_line,
                "operation": op_name,
            }

            if log_args:
                log_context["args"] = str(args)[:200] if args else None
                log_context["kwargs"] = str(kwargs)[:200] if kwargs else None

            try:
                logger.debug(
                    f"function_started",
                    **log_context
                )

                result = await func(*args, **kwargs)

                duration = time.perf_counter() - start_time
                duration_ms = round(duration * 1000, 2)
                span.set_attribute("duration_ms", duration_ms)
                span.set_attribute("file", log_context["file"])
                span.set_attribute("line", func_line)
                span.set_status(trace.Status(trace.StatusCode.OK))

                log_context["duration_ms"] = duration_ms
                log_context["duration_seconds"] = round(duration, 3)
                log_context["success"] = True

                if log_result:
                    log_context["result"] = str(result)[:200]

                logger.info(
                    f"function_completed",
                    **log_context
                )

                return result

            except Exception as e:
                duration = time.perf_counter() - start_time
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.record_exception(e)
                span.set_attribute("duration", duration)
                span.set_attribute("file", log_context["file"])
                span.set_attribute("line", func_line)

                log_context["duration"] = duration
                log_context["error"] = str(e)
                log_context["error_type"] = type(e).__name__
                log_context["success"] = False

                logger.error(
                    f"Failed {op_name}",
                    **log_context
                )
                raise

            finally:
                span.end()

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.perf_counter()
            span = tracer.start_span(op_name)

            log_context = {
                "function": func.__name__,
                "module": func.__module__,
                "file": func_file.split("/")[-1],
                "line": func_line,
                "operation": op_name,
            }

            if log_args:
                log_context["args"] = str(args)[:200] if args else None
                log_context["kwargs"] = str(kwargs)[:200] if kwargs else None

            try:
                logger.debug(
                    f"function_started",
                    **log_context
                )

                result = func(*args, **kwargs)

                duration = time.perf_counter() - start_time
                duration_ms = round(duration * 1000, 2)
                span.set_attribute("duration_ms", duration_ms)
                span.set_attribute("file", log_context["file"])
                span.set_attribute("line", func_line)
                span.set_status(trace.Status(trace.StatusCode.OK))

                log_context["duration_ms"] = duration_ms
                log_context["duration_seconds"] = round(duration, 3)
                log_context["success"] = True

                if log_result:
                    log_context["result"] = str(result)[:200]

                logger.info(
                    f"function_completed",
                    **log_context
                )

                return result

            except Exception as e:
                duration = time.perf_counter() - start_time
                duration_ms = round(duration * 1000, 2)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.record_exception(e)
                span.set_attribute("duration_ms", duration_ms)
                span.set_attribute("file", log_context["file"])
                span.set_attribute("line", func_line)

                log_context["duration_ms"] = duration_ms
                log_context["duration_seconds"] = round(duration, 3)
                log_context["error"] = str(e)
                log_context["error_type"] = type(e).__name__
                log_context["success"] = False

                logger.error(
                    f"function_failed",
                    **log_context
                )
                raise

            finally:
                span.end()

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def get_caller_info() -> dict[str, Any]:
    frame = inspect.currentframe()
    if not frame:
        return {"file": "unknown", "line": 0}

    caller_frame = frame.f_back
    if not caller_frame:
        return {"file": "unknown", "line": 0}

    return {
        "file": caller_frame.f_code.co_filename.split("/")[-1],
        "line": caller_frame.f_lineno,
        "function": caller_frame.f_code.co_name,
    }
