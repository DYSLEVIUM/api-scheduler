from uuid import UUID

from core.logging import get_logger
from db.database import get_session
from db.models.job import Job as JobModel
from models.job import Job as JobPydantic
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import delete, select

logger = get_logger()


class JobRepository:
    async def create_job(self, job: JobPydantic):
        logger.info("create_job_started", schedule_id=str(job.schedule_id), status=job.status)
        async with get_session() as session:
            try:
                db_job = job.to_db_model()
                session.add(db_job)
                await session.commit()
                await session.refresh(db_job)
                logger.info("create_job_success", job_id=str(db_job.id), schedule_id=str(db_job.schedule_id))
                return db_job
            except SQLAlchemyError as e:
                logger.error("create_job_db_error", error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                logger.error("create_job_error", error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(str(e))

    async def get_job_by_id(self, job_id: UUID):
        logger.debug("get_job_by_id_started", job_id=str(job_id))
        async with get_session() as session:
            try:
                result = await session.execute(
                    select(JobModel).where(JobModel.id == job_id)
                )
                job = result.scalar_one_or_none()
                if not job:
                    logger.warning("job_not_found", job_id=str(job_id))
                    raise Exception(f"Job with id {job_id} not found")
                return job
            except SQLAlchemyError as e:
                logger.error("get_job_db_error", job_id=str(job_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                if "not found" not in str(e).lower():
                    logger.error("get_job_error", job_id=str(job_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise

    async def get_jobs_by_schedule_id(
        self,
        schedule_id: UUID,
        status_filter=None,
        start_time=None,
        end_time=None,
    ):
        async with get_session() as session:
            try:
                query = select(JobModel).where(
                    JobModel.schedule_id == schedule_id)

                if status_filter:
                    query = query.where(JobModel.status == status_filter)

                if start_time:
                    query = query.where(JobModel.started_at >= start_time)

                if end_time:
                    query = query.where(JobModel.started_at <= end_time)

                query = query.order_by(JobModel.started_at.desc())

                result = await session.execute(query)
                return result.scalars().all()
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                raise Exception(str(e))

    async def get_all_jobs(self, status_filter=None, start_time=None, end_time=None):
        logger.debug("get_all_jobs_started", status_filter=status_filter, has_time_filter=bool(start_time or end_time))
        async with get_session() as session:
            try:
                query = select(JobModel)

                if status_filter:
                    query = query.where(JobModel.status == status_filter)

                if start_time:
                    query = query.where(JobModel.started_at >= start_time)

                if end_time:
                    query = query.where(JobModel.started_at <= end_time)

                query = query.order_by(JobModel.started_at.desc())

                result = await session.execute(query)
                jobs = result.scalars().all()
                logger.info("get_all_jobs_success", count=len(jobs), status_filter=status_filter)
                return jobs
            except SQLAlchemyError as e:
                logger.error("get_all_jobs_db_error", error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                logger.error("get_all_jobs_error", error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(str(e))

    async def delete_jobs_by_schedule_id(self, schedule_id: UUID):
        async with get_session() as session:
            try:
                result = await session.execute(
                    delete(JobModel)
                    .where(JobModel.schedule_id == schedule_id)
                    .returning(JobModel.id)
                )
                deleted_count = len(result.all())
                await session.commit()
                return deleted_count
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                raise Exception(str(e))
