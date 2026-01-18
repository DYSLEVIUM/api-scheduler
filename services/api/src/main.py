import asyncio
import logging
from contextlib import asynccontextmanager

import structlog
import uvicorn
from core.config import settings
from core.db_monitor import monitor_db_pool
from core.logging import setup_logging
from core.otel import setup_opentelemetry
from db.database import engine
from domains.health.router import router as health_router
from domains.runs.router import router as runs_router
from domains.schedules.router import router as schedules_router
from domains.targets.router import router as targets_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middleware.logging import LoggingMiddleware
from middleware.observability import ObservabilityMiddleware
from temporal.worker_service import temporal_worker_lifespan


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = setup_logging(
        log_level=settings.log_level,
    )

    setup_opentelemetry(
        service_name=settings.otel_service_name,
        otel_endpoint=settings.otel_endpoint,
    )

    logger.info(
        "application_starting",
        service=settings.otel_service_name,
        environment="development" if settings.dev else "production",
    )

    monitor_task = asyncio.create_task(monitor_db_pool(engine, interval_seconds=30))

    async with temporal_worker_lifespan():
        logger.info("application_ready")
        yield
        logger.info("application_shutting_down")
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass


def create_app():
    import logging

    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)

    app = FastAPI(
        title="API Scheduler",
        description="API Scheduler",
        version="0.1.0",
        redirect_slashes=True,
        lifespan=lifespan,
    )

    #! on production should separate public and private routers
    #! also make different services for the entities
    app.include_router(targets_router)
    app.include_router(health_router)
    app.include_router(schedules_router)
    app.include_router(runs_router)

    return app


app = create_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(ObservabilityMiddleware)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
