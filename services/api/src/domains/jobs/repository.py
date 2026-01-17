from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

from db.database import get_session
from db.models.job import Job as JobModel
from models.job import Job as JobPydantic


class JobRepository:
    async def create_job(self, job: JobPydantic):
        async with get_session() as session:
            try:
                db_job = job.to_db_model()
                session.add(db_job)
                await session.commit()
                await session.refresh(db_job)
                return db_job
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                raise Exception(str(e))

    async def get_job_by_id(self, job_id: UUID):
        async with get_session() as session:
            try:
                result = await session.execute(
                    select(JobModel).where(JobModel.id == job_id)
                )
                job = result.scalar_one_or_none()
                if not job:
                    raise Exception(f"Job with id {job_id} not found")
                return job
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                if "not found" in str(e).lower():
                    raise
                raise Exception(str(e))

    async def get_jobs_by_schedule_id(self, schedule_id: UUID):
        async with get_session() as session:
            try:
                result = await session.execute(
                    select(JobModel).where(JobModel.schedule_id == schedule_id)
                )
                return result.scalars().all()
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                raise Exception(str(e))

    async def get_all_jobs(self):
        async with get_session() as session:
            try:
                result = await session.execute(select(JobModel))
                return result.scalars().all()
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                raise Exception(str(e))
