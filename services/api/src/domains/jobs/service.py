from uuid import UUID

from core.logging import get_logger
from models.job import Job

from .repository import JobRepository

logger = get_logger()


class JobService:
    repository = JobRepository()

    async def create_job(self, job: Job):
        logger.info("service_create_job", schedule_id=str(job.schedule_id), status=job.status)
        try:
            db_job = await self.repository.create_job(job)
            return db_job.to_pydantic_model()
        except Exception as e:
            logger.error("service_create_job_error", error=str(e))
            raise Exception(str(e))

    async def get_job_by_id(self, job_id: UUID):
        logger.debug("service_get_job_by_id", job_id=str(job_id))
        try:
            db_job = await self.repository.get_job_by_id(job_id)
            return db_job.to_pydantic_model()
        except Exception as e:
            logger.error("service_get_job_by_id_error", job_id=str(job_id), error=str(e))
            raise Exception(str(e))

    async def get_jobs_by_schedule_id(
        self,
        schedule_id: UUID,
        status_filter=None,
        start_time=None,
        end_time=None,
    ):
        logger.debug("service_get_jobs_by_schedule", schedule_id=str(schedule_id), status_filter=status_filter)
        try:
            db_jobs = await self.repository.get_jobs_by_schedule_id(
                schedule_id, status_filter, start_time, end_time
            )
            return [db_job.to_pydantic_model() for db_job in db_jobs]
        except Exception as e:
            logger.error("service_get_jobs_by_schedule_error", schedule_id=str(schedule_id), error=str(e))
            raise Exception(str(e))

    async def get_all_jobs(self, status_filter=None, start_time=None, end_time=None):
        logger.debug("service_get_all_jobs", status_filter=status_filter)
        try:
            db_jobs = await self.repository.get_all_jobs(
                status_filter, start_time, end_time
            )
            return [db_job.to_pydantic_model() for db_job in db_jobs]
        except Exception as e:
            logger.error("service_get_all_jobs_error", error=str(e))
            raise Exception(str(e))
