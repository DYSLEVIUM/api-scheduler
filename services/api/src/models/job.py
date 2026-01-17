from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from db.models.job import Job as JobModel
from enums.job_status import JobStatus


class Job(BaseModel):
    id: UUID | None = None
    schedule_id: UUID | None = None
    run_number: int | None = None
    started_at: datetime | None = None
    status: JobStatus | None = None
    status_code: int | None = None
    latency_ms: float | None = None
    response_size_bytes: int | None = None
    request_headers: dict[str, str] | None = None
    request_body: dict[str, Any] | None = None
    response_headers: dict[str, str] | None = None
    response_body: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_db_model(self):
        job_data = self.model_dump(exclude_none=True, exclude={"id"})
        return JobModel(**job_data)

    def to_response(self):
        from domains.jobs.schemas import JobResponse
        job_data = self.model_dump()
        return JobResponse(**job_data)
