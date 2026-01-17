import asyncio
import logging
from contextlib import asynccontextmanager

from temporal.client import create_worker

logger = logging.getLogger(__name__)


class TemporalWorkerService:
    def __init__(self):
        self.worker = None
        self.worker_task = None

    async def start(self):
        if self.worker is not None:
            logger.warning("Worker already started")
            return

        try:
            self.worker = await create_worker()
            self.worker_task = asyncio.create_task(self.worker.run())
            logger.info("Temporal worker started")
        except Exception as e:
            logger.error(f"Failed to start Temporal worker: {e}")
            raise

    async def stop(self):
        if self.worker is None:
            return

        try:
            await self.worker.shutdown()
            if self.worker_task:
                await self.worker_task
            self.worker = None
            self.worker_task = None
            logger.info("Temporal worker stopped")
        except Exception as e:
            logger.error(f"Error stopping Temporal worker: {e}")


temporal_worker_service = TemporalWorkerService()


@asynccontextmanager
async def temporal_worker_lifespan():
    await temporal_worker_service.start()
    yield
    await temporal_worker_service.stop()
