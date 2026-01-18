import asyncio
from uuid import UUID

from core.decorators import log
from core.logging import get_logger
from db.database import get_session
from db.models.schedule import IntervalSchedule as IntervalScheduleModel
from db.models.schedule import Schedule as ScheduleModel
from db.models.schedule import WindowSchedule as WindowScheduleModel
from models.schedule import Schedule as SchedulePydantic
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import delete, select

logger = get_logger()


class ScheduleRepository:
    @log(operation_name="db.create_schedule", log_args=False)
    async def create_schedule(self, schedule: SchedulePydantic):
        async with get_session() as session:
            try:
                db_schedule = schedule.to_db_model()
                session.add(db_schedule)
                await session.commit()
                await session.refresh(db_schedule)
                logger.info("schedule_created", schedule_id=str(db_schedule.id), target_id=str(db_schedule.target_id))
                return db_schedule
            except SQLAlchemyError as e:
                logger.error("create_schedule_db_error", error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                logger.error("create_schedule_error", error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(str(e))

    async def _get_interval_schedule(self, schedule_id: UUID):
        async with get_session() as session:
            result = await session.execute(
                select(IntervalScheduleModel).where(
                    IntervalScheduleModel.id == schedule_id
                )
            )
            return result.scalar_one_or_none()

    async def _get_window_schedule(self, schedule_id: UUID):
        async with get_session() as session:
            result = await session.execute(
                select(WindowScheduleModel).where(
                    WindowScheduleModel.id == schedule_id
                )
            )
            return result.scalar_one_or_none()

    @log(operation_name="db.get_schedule_by_id", log_args=False)
    async def get_schedule_by_id(self, schedule_id: UUID):
        try:
            interval_schedule, window_schedule = await asyncio.gather(
                self._get_interval_schedule(schedule_id),
                self._get_window_schedule(schedule_id)
            )

            if interval_schedule:
                return interval_schedule

            if window_schedule:
                return window_schedule

            logger.warning("schedule_not_found", schedule_id=str(schedule_id))
            raise Exception(f"Schedule with id {schedule_id} not found")
        except SQLAlchemyError as e:
            logger.error("get_schedule_db_error", schedule_id=str(schedule_id), error=str(e), error_type=type(e).__name__, exc_info=True)
            raise Exception(f"Database error occurred: {str(e)}")
        except Exception as e:
            if "not found" not in str(e).lower():
                logger.error("get_schedule_error", schedule_id=str(schedule_id), error=str(e), error_type=type(e).__name__, exc_info=True)
            raise

    async def _get_all_interval_schedules(self):
        async with get_session() as session:
            result = await session.execute(select(IntervalScheduleModel))
            return result.scalars().all()

    async def _get_all_window_schedules(self):
        async with get_session() as session:
            result = await session.execute(select(WindowScheduleModel))
            return result.scalars().all()

    @log(operation_name="db.get_all_schedules")
    async def get_all_schedules(self):
        try:
            interval_schedules, window_schedules = await asyncio.gather(
                self._get_all_interval_schedules(),
                self._get_all_window_schedules()
            )
            return list(interval_schedules) + list(window_schedules)
        except SQLAlchemyError as e:
            raise Exception(f"Database error occurred: {str(e)}")
        except Exception as e:
            raise Exception(str(e))

    async def _get_interval_schedules_by_target(self, target_id: UUID):
        async with get_session() as session:
            result = await session.execute(
                select(IntervalScheduleModel).where(
                    IntervalScheduleModel.target_id == target_id
                )
            )
            return result.scalars().all()

    async def _get_window_schedules_by_target(self, target_id: UUID):
        async with get_session() as session:
            result = await session.execute(
                select(WindowScheduleModel).where(
                    WindowScheduleModel.target_id == target_id
                )
            )
            return result.scalars().all()

    @log(operation_name="db.get_schedules_by_target_id", log_args=False)
    async def get_schedules_by_target_id(self, target_id: UUID):
        try:
            interval_schedules, window_schedules = await asyncio.gather(
                self._get_interval_schedules_by_target(target_id),
                self._get_window_schedules_by_target(target_id)
            )
            return list(interval_schedules) + list(window_schedules)
        except SQLAlchemyError as e:
            raise Exception(f"Database error occurred: {str(e)}")
        except Exception as e:
            raise Exception(str(e))

    @log(operation_name="db.delete_schedules_by_target_id", log_args=False)
    async def delete_schedules_by_target_id(self, target_id: UUID):
        async with get_session() as session:
            try:
                await session.execute(
                    delete(IntervalScheduleModel).where(
                        IntervalScheduleModel.target_id == target_id
                    )
                )
                await session.execute(
                    delete(WindowScheduleModel).where(
                        WindowScheduleModel.target_id == target_id
                    )
                )
                await session.commit()
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                raise Exception(str(e))

    @log(operation_name="db.delete_schedule", log_args=False)
    async def delete_schedule(self, schedule_id: UUID):
        async with get_session() as session:
            try:
                schedule = await self.get_schedule_by_id(schedule_id)

                await session.delete(schedule)
                await session.commit()
                return schedule
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                raise Exception(str(e))

    @log(operation_name="db.pause_schedule", log_args=False)
    async def pause_schedule(self, schedule_id: UUID):
        async with get_session() as session:
            try:
                schedule = await self.get_schedule_by_id(schedule_id)

                schedule.paused = True
                schedule.temporal_workflow_id = None
                session.add(schedule)
                await session.commit()
                await session.refresh(schedule)
                return schedule
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                raise Exception(str(e))

    @log(operation_name="db.resume_schedule", log_args=False)
    async def resume_schedule(self, schedule_id: UUID):
        async with get_session() as session:
            try:
                schedule = await self.get_schedule_by_id(schedule_id)

                schedule.paused = False
                session.add(schedule)
                await session.commit()
                await session.refresh(schedule)
                return schedule
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                raise Exception(str(e))

    @log(operation_name="db.update_schedule", log_args=False)
    async def update_schedule(self, schedule_id: UUID, schedule: SchedulePydantic):
        async with get_session() as session:
            try:
                existing_schedule = await self.get_schedule_by_id(schedule_id)

                existing_schedule.interval_seconds = schedule.interval_seconds
                session.add(existing_schedule)
                await session.commit()
                await session.refresh(existing_schedule)
                return existing_schedule
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                raise Exception(str(e))

    @log(operation_name="db.update_workflow_id", log_args=False)
    async def update_workflow_id(self, schedule_id: UUID, workflow_id: str):
        async with get_session() as session:
            try:
                schedule = await self.get_schedule_by_id(schedule_id)
                schedule.temporal_workflow_id = workflow_id
                session.add(schedule)
                await session.commit()
                await session.refresh(schedule)
                return schedule
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                raise Exception(str(e))
