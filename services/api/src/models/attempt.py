from datetime import datetime
from typing import Any
from uuid import UUID

from enums.job_status import JobStatus
from pydantic import BaseModel, field_validator


class Attempt(BaseModel):
    id: UUID
    job_id: UUID
    attempt_number: int
    started_at: datetime
    status: JobStatus
    status_code: int | None = None
    latency_ms: float | None = None
    response_size_bytes: int | None = None
    response_headers: dict[str, str] | None = None
    response_body: dict[str, Any] | str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

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
