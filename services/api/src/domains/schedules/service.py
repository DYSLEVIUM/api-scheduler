from typing import List
from uuid import UUID

from core.decorators import log
from domains.jobs.repository import JobRepository
from models.schedule import Schedule
from temporal.client import get_temporal_client, start_schedule_workflow

from .repository import ScheduleRepository


class ScheduleService:
    repository = ScheduleRepository()

    @log(operation_name="service.create_schedule", log_args=False)
    async def create_schedule(self, schedule: Schedule):
        try:
            db_schedule = await self.repository.create_schedule(schedule)

            if not db_schedule.paused:
                client = await get_temporal_client()
                workflow_id = await start_schedule_workflow(
                    db_schedule.id, db_schedule.get_workflow_type(), client
                )
                await self.repository.update_workflow_id(db_schedule.id, workflow_id)

            return db_schedule.to_pydantic_model()
        except Exception as e:
            raise Exception(str(e))

    @log(operation_name="service.get_schedule_by_id", log_args=False)
    async def get_schedule_by_id(self, schedule_id: UUID):
        try:
            db_schedule = await self.repository.get_schedule_by_id(schedule_id)
            return db_schedule.to_pydantic_model()
        except Exception as e:
            raise Exception(str(e))

    @log(operation_name="service.get_all_schedules")
    async def get_all_schedules(self):
        try:
            db_schedules = await self.repository.get_all_schedules()
            return [db_schedule.to_pydantic_model() for db_schedule in db_schedules]
        except Exception as e:
            raise Exception(str(e))

    @log(operation_name="service.delete_schedule", log_args=False)
    async def delete_schedule(self, schedule_id: UUID):
        try:
            db_schedule = await self.repository.get_schedule_by_id(schedule_id)

            if db_schedule.temporal_workflow_id:
                from temporal.client import terminate_schedule_workflow
                client = await get_temporal_client()
                try:
                    await terminate_schedule_workflow(schedule_id, client)
                except Exception:
                    pass

            job_repo = JobRepository()
            await job_repo.delete_jobs_by_schedule_id(schedule_id)

            db_schedule = await self.repository.delete_schedule(schedule_id)
            return db_schedule.to_pydantic_model()
        except Exception as e:
            raise Exception(str(e))

    @log(operation_name="service.pause_schedule", log_args=False)
    async def pause_schedule(self, schedule_id: UUID):
        try:
            db_schedule = await self.repository.get_schedule_by_id(schedule_id)

            if db_schedule.temporal_workflow_id:
                from temporal.client import terminate_schedule_workflow
                client = await get_temporal_client()
                try:
                    await terminate_schedule_workflow(schedule_id, client)
                except Exception:
                    pass

            db_schedule = await self.repository.pause_schedule(schedule_id)
            return db_schedule.to_pydantic_model()
        except Exception as e:
            raise Exception(str(e))

    @log(operation_name="service.resume_schedule", log_args=False)
    async def resume_schedule(self, schedule_id: UUID):
        try:
            db_schedule = await self.repository.resume_schedule(schedule_id)

            client = await get_temporal_client()
            if db_schedule.temporal_workflow_id:
                try:
                    workflow_id = f"schedule-{schedule_id}"
                    handle = client.get_workflow_handle(workflow_id)
                    await handle.describe()
                except Exception:
                    workflow_id = await start_schedule_workflow(
                        schedule_id, db_schedule.get_workflow_type(), client
                    )
                    await self.repository.update_workflow_id(schedule_id, workflow_id)
            else:
                workflow_id = await start_schedule_workflow(
                    schedule_id, db_schedule.get_workflow_type(), client
                )
                await self.repository.update_workflow_id(schedule_id, workflow_id)
            return db_schedule.to_pydantic_model()
        except Exception as e:
            raise Exception(str(e))

    @log(operation_name="service.update_schedule", log_args=False)
    async def update_schedule(self, schedule_id: UUID, schedule: Schedule):
        try:
            db_schedule = await self.repository.update_schedule(schedule_id, schedule)
            return db_schedule.to_pydantic_model()
        except Exception as e:
            raise Exception(str(e))
