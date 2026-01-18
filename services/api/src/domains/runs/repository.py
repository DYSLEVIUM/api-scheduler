import asyncio
from datetime import datetime
from uuid import UUID

from core.logging import get_logger
from db.database import get_session
from db.models.attempt import Attempt
from db.models.job import Job as JobModel
from db.models.schedule import IntervalSchedule, WindowSchedule
from enums.job_status import JobStatus
from sqlalchemy import case, func
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

logger = get_logger()


class RunRepository:
    async def _get_run(self, run_id: UUID):
        async with get_session() as session:
            result = await session.execute(
                select(JobModel).where(JobModel.id == run_id)
            )
            return result.scalar_one_or_none()

    async def _get_attempts(self, run_id: UUID):
        async with get_session() as session:
            result = await session.execute(
                select(Attempt)
                .where(Attempt.job_id == run_id)
                .order_by(Attempt.attempt_number)
            )
            return result.scalars().all()

    async def get_run_by_id(self, run_id: UUID):
        logger.debug("get_run_by_id_started", run_id=str(run_id))
        try:
            run, attempts = await asyncio.gather(
                self._get_run(run_id),
                self._get_attempts(run_id)
            )

            if not run:
                logger.warning("run_not_found", run_id=str(run_id))
                raise Exception(f"Run with id {run_id} not found")

            logger.info("get_run_by_id_success", run_id=str(run_id), attempts_count=len(attempts), status=run.status)
            return run, attempts
        except SQLAlchemyError as e:
            logger.error("get_run_db_error", run_id=str(run_id), error=str(e), error_type=type(e).__name__, exc_info=True)
            raise Exception(f"Database error occurred: {str(e)}")
        except Exception as e:
            if "not found" not in str(e).lower():
                logger.error("get_run_error", run_id=str(run_id), error=str(e), error_type=type(e).__name__, exc_info=True)
            raise

    async def get_runs_by_schedule_id(
        self,
        schedule_id: UUID,
        status_filter: JobStatus | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ):
        async with get_session() as session:
            try:
                interval_subquery = select(
                    IntervalSchedule.id,
                    IntervalSchedule.name
                ).subquery()

                window_subquery = select(
                    WindowSchedule.id,
                    WindowSchedule.name
                ).subquery()

                name_expr = case(
                    (JobModel.schedule_id == interval_subquery.c.id,
                     interval_subquery.c.name),
                    (JobModel.schedule_id == window_subquery.c.id,
                     window_subquery.c.name),
                    else_=None
                ).label('name')

                query = select(JobModel, name_expr).where(
                    JobModel.schedule_id == schedule_id
                ).outerjoin(
                    interval_subquery, JobModel.schedule_id == interval_subquery.c.id
                ).outerjoin(
                    window_subquery, JobModel.schedule_id == window_subquery.c.id
                )

                if status_filter:
                    query = query.where(JobModel.status == status_filter)

                if start_time:
                    query = query.where(JobModel.started_at >= start_time)

                if end_time:
                    query = query.where(JobModel.started_at <= end_time)

                query = query.order_by(JobModel.run_number.desc())

                result = await session.execute(query)
                rows = result.all()

                jobs = []
                for row in rows:
                    job = row[0]
                    name = row[1]
                    jobs.append((job, name))

                return jobs
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                raise Exception(str(e))

    async def get_all_runs(
        self,
        status_filter: JobStatus | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ):
        async with get_session() as session:
            try:
                interval_subquery = select(
                    IntervalSchedule.id,
                    IntervalSchedule.name
                ).subquery()

                window_subquery = select(
                    WindowSchedule.id,
                    WindowSchedule.name
                ).subquery()

                name_expr = case(
                    (JobModel.schedule_id == interval_subquery.c.id,
                     interval_subquery.c.name),
                    (JobModel.schedule_id == window_subquery.c.id,
                     window_subquery.c.name),
                    else_=None
                ).label('name')

                query = select(JobModel, name_expr).outerjoin(
                    interval_subquery, JobModel.schedule_id == interval_subquery.c.id
                ).outerjoin(
                    window_subquery, JobModel.schedule_id == window_subquery.c.id
                )

                if status_filter:
                    query = query.where(JobModel.status == status_filter)

                if start_time:
                    query = query.where(JobModel.started_at >= start_time)

                if end_time:
                    query = query.where(JobModel.started_at <= end_time)

                query = query.order_by(JobModel.run_number.desc())

                result = await session.execute(query)
                rows = result.all()

                jobs = []
                for row in rows:
                    job = row[0]
                    name = row[1]
                    jobs.append((job, name))

                return jobs
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                raise Exception(str(e))
