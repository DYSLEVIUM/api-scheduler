from datetime import datetime
from uuid import UUID

from enums.job_status import JobStatus

from .repository import RunRepository


class RunService:
    repository = RunRepository()

    async def get_run_by_id(self, run_id: UUID):
        try:
            db_run, db_attempts = await self.repository.get_run_by_id(run_id)
            run_pydantic = db_run.to_pydantic_model()

            if db_attempts:
                attempts_pydantic = [attempt.to_pydantic_model()
                                     for attempt in db_attempts]
                run_dict = run_pydantic.model_dump()
                run_dict['attempts'] = attempts_pydantic
                from models.job import Job as JobPydantic
                return JobPydantic(**run_dict)

            return run_pydantic
        except Exception as e:
            raise Exception(str(e))

    async def get_runs_by_schedule_id(
        self,
        schedule_id: UUID,
        status_filter: JobStatus | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ):
        try:
            runs = await self.repository.get_runs_by_schedule_id(
                schedule_id, status_filter, start_time, end_time
            )
            result = []
            for db_run, name in runs:
                run_pydantic = db_run.to_pydantic_model()
                run_dict = run_pydantic.model_dump()
                run_dict['name'] = name
                from models.job import Job as JobPydantic
                result.append(JobPydantic(**run_dict))
            return result
        except Exception as e:
            raise Exception(str(e))

    async def get_all_runs(
        self,
        status_filter: JobStatus | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ):
        try:
            runs = await self.repository.get_all_runs(
                status_filter, start_time, end_time
            )
            result = []
            for db_run, name in runs:
                run_pydantic = db_run.to_pydantic_model()
                run_dict = run_pydantic.model_dump()
                run_dict['name'] = name
                from models.job import Job as JobPydantic
                result.append(JobPydantic(**run_dict))
            return result
        except Exception as e:
            raise Exception(str(e))
