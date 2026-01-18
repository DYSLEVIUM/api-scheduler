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
                logger.info("schedule_created", schedule_id=str(
                    db_schedule.id), target_id=str(db_schedule.target_id))
                return db_schedule
            except SQLAlchemyError as e:
                logger.error("create_schedule_db_error", error=str(
                    e), error_type=type(e).__name__, exc_info=True)
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                logger.error("create_schedule_error", error=str(
                    e), error_type=type(e).__name__, exc_info=True)
                raise Exception(str(e))

    @log(operation_name="db.get_schedule_by_id", log_args=False)
    async def get_schedule_by_id(self, schedule_id: UUID):
        async with get_session() as session:
            try:
                interval_result = await session.execute(
                    select(IntervalScheduleModel).where(
                        IntervalScheduleModel.id == schedule_id
                    )
                )
                interval_schedule = interval_result.scalar_one_or_none()

                if interval_schedule:
                    logger.debug("interval_schedule_found",
                                 schedule_id=str(schedule_id))
                    return interval_schedule

                window_result = await session.execute(
                    select(WindowScheduleModel).where(
                        WindowScheduleModel.id == schedule_id
                    )
                )
                window_schedule = window_result.scalar_one_or_none()

                if window_schedule:
                    logger.debug("window_schedule_found",
                                 schedule_id=str(schedule_id))
                    return window_schedule

                logger.warning("schedule_not_found",
                               schedule_id=str(schedule_id))
                raise Exception(f"Schedule with id {schedule_id} not found")
            except SQLAlchemyError as e:
                logger.error("get_schedule_db_error", schedule_id=str(
                    schedule_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                if "not found" not in str(e).lower():
                    logger.error("get_schedule_error", schedule_id=str(
                        schedule_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise

    @log(operation_name="db.get_all_schedules")
    async def get_all_schedules(self):
        async with get_session() as session:
            try:
                interval_result = await session.execute(select(IntervalScheduleModel))
                interval_schedules = interval_result.scalars().all()

                window_result = await session.execute(select(WindowScheduleModel))
                window_schedules = window_result.scalars().all()

                all_schedules = list(interval_schedules) + \
                    list(window_schedules)
                logger.info("get_all_schedules_success",
                            count=len(all_schedules))
                return all_schedules
            except SQLAlchemyError as e:
                logger.error("get_all_schedules_db_error", error=str(
                    e), error_type=type(e).__name__, exc_info=True)
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                logger.error("get_all_schedules_error", error=str(
                    e), error_type=type(e).__name__, exc_info=True)
                raise Exception(str(e))

    @log(operation_name="db.get_schedules_by_target_id", log_args=False)
    async def get_schedules_by_target_id(self, target_id: UUID):
        async with get_session() as session:
            try:
                interval_result = await session.execute(
                    select(IntervalScheduleModel).where(
                        IntervalScheduleModel.target_id == target_id
                    )
                )
                interval_schedules = interval_result.scalars().all()

                window_result = await session.execute(
                    select(WindowScheduleModel).where(
                        WindowScheduleModel.target_id == target_id
                    )
                )
                window_schedules = window_result.scalars().all()

                schedules = list(interval_schedules) + list(window_schedules)
                logger.info("get_schedules_by_target_success",
                            target_id=str(target_id), count=len(schedules))
                return schedules
            except SQLAlchemyError as e:
                logger.error("get_schedules_by_target_db_error", target_id=str(
                    target_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                logger.error("get_schedules_by_target_error", target_id=str(
                    target_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(str(e))

    @log(operation_name="db.delete_schedules_by_target_id", log_args=False)
    async def delete_schedules_by_target_id(self, target_id: UUID):
        async with get_session() as session:
            try:
                interval_result = await session.execute(
                    delete(IntervalScheduleModel).where(
                        IntervalScheduleModel.target_id == target_id
                    ).returning(IntervalScheduleModel.id)
                )
                interval_count = len(interval_result.all())

                window_result = await session.execute(
                    delete(WindowScheduleModel).where(
                        WindowScheduleModel.target_id == target_id
                    ).returning(WindowScheduleModel.id)
                )
                window_count = len(window_result.all())

                await session.commit()
                logger.info("delete_schedules_by_target_success", target_id=str(
                    target_id), deleted_count=interval_count + window_count)
            except SQLAlchemyError as e:
                logger.error("delete_schedules_by_target_db_error", target_id=str(
                    target_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                logger.error("delete_schedules_by_target_error", target_id=str(
                    target_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(str(e))

    @log(operation_name="db.delete_schedule", log_args=False)
    async def delete_schedule(self, schedule_id: UUID):
        async with get_session() as session:
            try:
                interval_result = await session.execute(
                    select(IntervalScheduleModel).where(
                        IntervalScheduleModel.id == schedule_id
                    )
                )
                schedule = interval_result.scalar_one_or_none()

                if not schedule:
                    window_result = await session.execute(
                        select(WindowScheduleModel).where(
                            WindowScheduleModel.id == schedule_id
                        )
                    )
                    schedule = window_result.scalar_one_or_none()

                if not schedule:
                    logger.warning("delete_schedule_not_found",
                                   schedule_id=str(schedule_id))
                    raise Exception(
                        f"Schedule with id {schedule_id} not found")

                await session.delete(schedule)
                await session.commit()
                logger.info("delete_schedule_success",
                            schedule_id=str(schedule_id))
                return schedule
            except SQLAlchemyError as e:
                logger.error("delete_schedule_db_error", schedule_id=str(
                    schedule_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                if "not found" not in str(e).lower():
                    logger.error("delete_schedule_error", schedule_id=str(
                        schedule_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(str(e))

    @log(operation_name="db.pause_schedule", log_args=False)
    async def pause_schedule(self, schedule_id: UUID):
        async with get_session() as session:
            try:
                interval_result = await session.execute(
                    select(IntervalScheduleModel).where(
                        IntervalScheduleModel.id == schedule_id
                    )
                )
                schedule = interval_result.scalar_one_or_none()

                if not schedule:
                    window_result = await session.execute(
                        select(WindowScheduleModel).where(
                            WindowScheduleModel.id == schedule_id
                        )
                    )
                    schedule = window_result.scalar_one_or_none()

                if not schedule:
                    logger.warning("pause_schedule_not_found",
                                   schedule_id=str(schedule_id))
                    raise Exception(
                        f"Schedule with id {schedule_id} not found")

                schedule.paused = True
                schedule.temporal_workflow_id = None
                session.add(schedule)
                await session.commit()
                await session.refresh(schedule)
                logger.info("pause_schedule_success",
                            schedule_id=str(schedule_id))
                return schedule
            except SQLAlchemyError as e:
                logger.error("pause_schedule_db_error", schedule_id=str(
                    schedule_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                if "not found" not in str(e).lower():
                    logger.error("pause_schedule_error", schedule_id=str(
                        schedule_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(str(e))

    @log(operation_name="db.resume_schedule", log_args=False)
    async def resume_schedule(self, schedule_id: UUID):
        async with get_session() as session:
            try:
                interval_result = await session.execute(
                    select(IntervalScheduleModel).where(
                        IntervalScheduleModel.id == schedule_id
                    )
                )
                schedule = interval_result.scalar_one_or_none()

                if not schedule:
                    window_result = await session.execute(
                        select(WindowScheduleModel).where(
                            WindowScheduleModel.id == schedule_id
                        )
                    )
                    schedule = window_result.scalar_one_or_none()

                if not schedule:
                    logger.warning("resume_schedule_not_found",
                                   schedule_id=str(schedule_id))
                    raise Exception(
                        f"Schedule with id {schedule_id} not found")

                schedule.paused = False
                session.add(schedule)
                await session.commit()
                await session.refresh(schedule)
                logger.info("resume_schedule_success",
                            schedule_id=str(schedule_id))
                return schedule
            except SQLAlchemyError as e:
                logger.error("resume_schedule_db_error", schedule_id=str(
                    schedule_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                if "not found" not in str(e).lower():
                    logger.error("resume_schedule_error", schedule_id=str(
                        schedule_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(str(e))

    @log(operation_name="db.update_schedule", log_args=False)
    async def update_schedule(self, schedule_id: UUID, schedule: SchedulePydantic):
        async with get_session() as session:
            try:
                interval_result = await session.execute(
                    select(IntervalScheduleModel).where(
                        IntervalScheduleModel.id == schedule_id
                    )
                )
                existing_schedule = interval_result.scalar_one_or_none()

                if not existing_schedule:
                    window_result = await session.execute(
                        select(WindowScheduleModel).where(
                            WindowScheduleModel.id == schedule_id
                        )
                    )
                    existing_schedule = window_result.scalar_one_or_none()

                if not existing_schedule:
                    logger.warning("update_schedule_not_found",
                                   schedule_id=str(schedule_id))
                    raise Exception(
                        f"Schedule with id {schedule_id} not found")

                existing_schedule.interval_seconds = schedule.interval_seconds
                session.add(existing_schedule)
                await session.commit()
                await session.refresh(existing_schedule)
                logger.info("update_schedule_success",
                            schedule_id=str(schedule_id))
                return existing_schedule
            except SQLAlchemyError as e:
                logger.error("update_schedule_db_error", schedule_id=str(
                    schedule_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                if "not found" not in str(e).lower():
                    logger.error("update_schedule_error", schedule_id=str(
                        schedule_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(str(e))

    @log(operation_name="db.update_workflow_id", log_args=False)
    async def update_workflow_id(self, schedule_id: UUID, workflow_id: str):
        async with get_session() as session:
            try:
                interval_result = await session.execute(
                    select(IntervalScheduleModel).where(
                        IntervalScheduleModel.id == schedule_id
                    )
                )
                schedule = interval_result.scalar_one_or_none()

                if not schedule:
                    window_result = await session.execute(
                        select(WindowScheduleModel).where(
                            WindowScheduleModel.id == schedule_id
                        )
                    )
                    schedule = window_result.scalar_one_or_none()

                if not schedule:
                    logger.warning("update_workflow_id_not_found",
                                   schedule_id=str(schedule_id))
                    raise Exception(
                        f"Schedule with id {schedule_id} not found")

                schedule.temporal_workflow_id = workflow_id
                session.add(schedule)
                await session.commit()
                await session.refresh(schedule)
                logger.info("update_workflow_id_success", schedule_id=str(
                    schedule_id), workflow_id=workflow_id)
                return schedule
            except SQLAlchemyError as e:
                logger.error("update_workflow_id_db_error", schedule_id=str(
                    schedule_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                if "not found" not in str(e).lower():
                    logger.error("update_workflow_id_error", schedule_id=str(
                        schedule_id), error=str(e), error_type=type(e).__name__, exc_info=True)
                raise Exception(str(e))
