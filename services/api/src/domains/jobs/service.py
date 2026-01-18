from uuid import UUID

from models.job import Job

from .repository import JobRepository


class JobService:
    repository = JobRepository()

    async def create_job(self, job: Job):
        try:
            db_job = await self.repository.create_job(job)
            return db_job.to_pydantic_model()
        except Exception as e:
            raise Exception(str(e))

    async def get_job_by_id(self, job_id: UUID):
        try:
            db_job = await self.repository.get_job_by_id(job_id)
            return db_job.to_pydantic_model()
        except Exception as e:
            raise Exception(str(e))

    async def get_jobs_by_schedule_id(
        self,
        schedule_id: UUID,
        status_filter=None,
        start_time=None,
        end_time=None,
    ):
        try:
            db_jobs = await self.repository.get_jobs_by_schedule_id(
                schedule_id, status_filter, start_time, end_time
            )
            return [db_job.to_pydantic_model() for db_job in db_jobs]
        except Exception as e:
            raise Exception(str(e))

    async def get_all_jobs(self, status_filter=None, start_time=None, end_time=None):
        try:
            db_jobs = await self.repository.get_all_jobs(
                status_filter, start_time, end_time
            )
            return [db_job.to_pydantic_model() for db_job in db_jobs]
        except Exception as e:
            raise Exception(str(e))
