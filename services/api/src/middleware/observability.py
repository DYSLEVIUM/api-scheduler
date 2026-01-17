import time
from typing import Callable

from fastapi import Request, Response
from opentelemetry import trace
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware

from core.logging import get_logger
from core.metrics import (
    http_request_duration_seconds,
    http_requests_total,
    http_request_size_bytes,
    http_response_size_bytes,
)
from core.otel import get_tracer

logger = get_logger()
tracer = get_tracer()


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        span = tracer.start_span(f"{request.method} {request.url.path}")

        try:
            req_body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    req_body = body.decode("utf-8") if body else None
                    request._body = body
                except Exception:
                    pass

            request_size = len(req_body.encode("utf-8")) if req_body else 0

            response = await call_next(request)

            process_time = time.perf_counter() - start_time
            status_code = response.status_code

            res_body = [section async for section in response.body_iterator]
            response.body_iterator = iterate_in_threadpool(iter(res_body))
            res_body_bytes = b"".join(res_body)
            response_size = len(res_body_bytes)

            endpoint = request.url.path
            method = request.method

            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()

            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).observe(process_time)

            http_request_size_bytes.labels(
                method=method,
                endpoint=endpoint
            ).observe(request_size)

            http_response_size_bytes.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).observe(response_size)

            log_data = {
                "method": method,
                "path": endpoint,
                "status_code": status_code,
                "process_time": process_time,
                "request_size": request_size,
                "response_size": response_size,
                "client_ip": request.client.host if request.client else None,
            }

            logger.info(
                f"{method} {endpoint}",
                **log_data
            )

            span.set_attribute("http.method", method)
            span.set_attribute("http.path", endpoint)
            span.set_attribute("http.status_code", status_code)
            span.set_attribute("http.duration", process_time)
            span.set_attribute("http.request_size", request_size)
            span.set_attribute("http.response_size", response_size)

            if status_code >= 400:
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                logger.warning(
                    f"{method} {endpoint} returned {status_code}",
                    **log_data
                )
            else:
                span.set_status(trace.Status(trace.StatusCode.OK))

            return response

        except Exception as e:
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error(
                f"Error processing {request.method} {request.url.path}",
                error=str(e),
                method=request.method,
                path=request.url.path,
            )
            raise
        finally:
            span.end()
