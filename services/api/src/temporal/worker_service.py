import asyncio
from contextlib import asynccontextmanager

from core.logging import get_logger
from temporal.client import create_worker

logger = get_logger()


class TemporalWorkerService:
    def __init__(self):
        self.worker = None
        self.worker_task = None

    async def start(self):
        if self.worker is not None:
            logger.warning("temporal_worker_already_started")
            return

        try:
            logger.info("temporal_worker_starting")
            self.worker = await create_worker()
            self.worker_task = asyncio.create_task(self.worker.run())
            logger.info(
                "temporal_worker_started",
                worker_id=id(self.worker),
                task_id=id(self.worker_task),
            )
        except Exception as e:
            logger.error(
                "temporal_worker_start_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            raise

    async def stop(self):
        if self.worker is None:
            return

        try:
            logger.info("temporal_worker_stopping")
            await self.worker.shutdown()
            if self.worker_task:
                await self.worker_task
            self.worker = None
            self.worker_task = None
            logger.info("temporal_worker_stopped")
        except Exception as e:
            logger.error(
                "temporal_worker_stop_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )


temporal_worker_service = TemporalWorkerService()


@asynccontextmanager
async def temporal_worker_lifespan():
    await temporal_worker_service.start()
    yield
    await temporal_worker_service.stop()
