from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from db.models.job import Job as JobModel
from enums.job_status import JobStatus
from models.attempt import Attempt
from pydantic import BaseModel, field_validator


class Job(BaseModel):
    id: UUID | None = None
    schedule_id: UUID | None = None
    name: str | None = None
    run_number: int | None = None
    started_at: datetime | None = None
    status: JobStatus | None = None
    status_code: int | None = None
    latency_ms: float | None = None
    response_size_bytes: int | None = None
    request_headers: dict[str, str] | None = None
    request_body: dict[str, Any] | None = None
    response_headers: dict[str, str] | None = None
    response_body: dict[str, Any] | str | None = None
    error_message: str | None = None
    redirected: bool = False
    redirect_count: int = 0
    redirect_history: list[dict[str, Any]] | None = None
    attempts: list[Attempt] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator('response_body', mode='before')
    @classmethod
    def validate_response_body(cls, v):
        if v is None:
            return v
        if isinstance(v, (dict, str)):
            return v
        if isinstance(v, (list, int, float, bool)):
            return v
        return str(v)

    def to_db_model(self):
        job_data = self.model_dump(exclude_none=True, exclude={"id"})
        return JobModel(**job_data)

    def to_response(self):
        from domains.jobs.schemas import JobResponse
        job_data = self.model_dump()
        return JobResponse(**job_data)


Job.model_rebuild()
