import logging
from contextlib import asynccontextmanager

import uvicorn
from core.config import settings
from core.logging import setup_logging
from core.otel import setup_opentelemetry
from domains.health.router import router as health_router
from domains.jobs.router import router as jobs_router
from domains.schedules.router import router as schedules_router
from domains.schedules.service import ScheduleService
from domains.targets.router import router as targets_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middleware.observability import ObservabilityMiddleware
from temporal.client import get_temporal_client, start_schedule_workflow
from temporal.worker_service import temporal_worker_lifespan

logger = logging.getLogger(__name__)


async def resume_existing_schedules():
    schedule_service = ScheduleService()
    db_schedules = await schedule_service.repository.get_all_schedules()

    client = await get_temporal_client()

    try:
        for db_schedule in db_schedules:
            if db_schedule.paused or db_schedule.temporal_workflow_id:
                continue

            try:
                workflow_id = await start_schedule_workflow(
                    db_schedule.id, db_schedule.get_workflow_type(), client
                )
                await schedule_service.repository.update_workflow_id(
                    db_schedule.id, workflow_id
                )
            except Exception:
                pass
    finally:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(
        fluentd_host=settings.fluentd_host,
        fluentd_port=settings.fluentd_port,
        log_level=settings.log_level,
        enable_fluentd=settings.enable_fluentd,
    )

    setup_opentelemetry(
        service_name=settings.otel_service_name,
        otel_endpoint=settings.otel_endpoint,
    )

    async with temporal_worker_lifespan():
        await resume_existing_schedules()
        yield


def create_app():
    import logging

    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)

    app = FastAPI(
        title="API Scheduler",
        description="API Scheduler",
        version="0.1.0",
        redirect_slashes=False,
        lifespan=lifespan,
    )

    #! on production should separate public and private routers
    #! also make different services for the entities
    app.include_router(targets_router)
    app.include_router(health_router)
    app.include_router(schedules_router)
    app.include_router(jobs_router)

    return app


app = create_app()

origins = [
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ObservabilityMiddleware)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
