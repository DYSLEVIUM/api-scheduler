from datetime import datetime
from typing import Any
from uuid import UUID

from enums.job_status import JobStatus
from pydantic import BaseModel, field_validator


class AttemptResponse(BaseModel):
    id: UUID
    attempt_number: int
    started_at: datetime
    status: JobStatus
    status_code: int | None
    latency_ms: float | None
    response_size_bytes: int | None
    response_headers: dict[str, str] | None
    response_body: dict[str, Any] | str | None
    error_message: str | None
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


class RunResponse(BaseModel):
    id: UUID
    schedule_id: UUID
    name: str | None = None
    run_number: int
    started_at: datetime
    status: JobStatus
    status_code: int | None
    latency_ms: float | None
    response_size_bytes: int | None
    request_headers: dict[str, str] | None
    request_body: dict[str, Any] | None
    response_headers: dict[str, str] | None
    response_body: dict[str, Any] | str | None
    error_message: str | None
    redirected: bool | None = None
    redirect_count: int | None = None
    redirect_history: list[dict[str, Any]] | None = None
    attempts: list[AttemptResponse] | None = None
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
