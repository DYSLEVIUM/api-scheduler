from uuid import UUID

from core.decorators import log
from db.database import get_session
from db.models.schedule import IntervalSchedule as IntervalScheduleModel
from db.models.schedule import Schedule as ScheduleModel
from db.models.schedule import WindowSchedule as WindowScheduleModel
from models.schedule import Schedule as SchedulePydantic
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select


class ScheduleRepository:
    @log(operation_name="db.create_schedule", log_args=False)
    async def create_schedule(self, schedule: SchedulePydantic):
        async with get_session() as session:
            try:
                db_schedule = schedule.to_db_model()
                session.add(db_schedule)
                await session.commit()
                await session.refresh(db_schedule)
                return db_schedule
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
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
                    return interval_schedule

                window_result = await session.execute(
                    select(WindowScheduleModel).where(
                        WindowScheduleModel.id == schedule_id
                    )
                )
                window_schedule = window_result.scalar_one_or_none()

                if window_schedule:
                    return window_schedule

                raise Exception(f"Schedule with id {schedule_id} not found")
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                if "not found" in str(e).lower():
                    raise

    @log(operation_name="db.get_all_schedules")
    async def get_all_schedules(self):
        async with get_session() as session:
            try:
                interval_result = await session.execute(
                    select(IntervalScheduleModel)
                )
                interval_schedules = interval_result.scalars().all()

                window_result = await session.execute(
                    select(WindowScheduleModel)
                )
                window_schedules = window_result.scalars().all()

                return list(interval_schedules) + list(window_schedules)
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
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

                return list(interval_schedules) + list(window_schedules)
            except SQLAlchemyError as e:
                raise Exception(f"Database error occurred: {str(e)}")
            except Exception as e:
                raise Exception(str(e))

    @log(operation_name="db.delete_schedules_by_target_id", log_args=False)
    async def delete_schedules_by_target_id(self, target_id: UUID):
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

                for schedule in interval_schedules:
                    await session.delete(schedule)
                for schedule in window_schedules:
                    await session.delete(schedule)
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
