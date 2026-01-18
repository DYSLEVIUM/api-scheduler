from datetime import datetime
from typing import Any
from uuid import UUID

from db.mixins.timestamp import TimestampMixin
from db.mixins.uuid import UUIDMixin
from enums.job_status import JobStatus
from sqlalchemy import JSON, Column, TypeDecorator
from sqlalchemy.dialects.postgresql import ENUM
from sqlmodel import Field


class JobStatusEnum(TypeDecorator):
    impl = ENUM(
        "success",
        "timeout",
        "dns_error",
        "connection_error",
        "http_4xx",
        "http_5xx",
        "error",
        name="jobstatus",
        create_type=False
    )
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, JobStatus):
            return value.value
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return JobStatus(value)


class Job(UUIDMixin, TimestampMixin, table=True):
    __tablename__ = "jobs"

    schedule_id: UUID = Field(nullable=False, index=True)
    run_number: int = Field(nullable=False)
    started_at: datetime = Field(nullable=False)
    status: JobStatus = Field(
        sa_column=Column(JobStatusEnum(), nullable=False)
    )
    status_code: int | None = Field(default=None)
    latency_ms: float | None = Field(default=None)
    response_size_bytes: int | None = Field(default=None)
    request_headers: Any = Field(default=None, sa_column=Column(JSON))
    request_body: Any = Field(default=None, sa_column=Column(JSON))
    response_headers: Any = Field(default=None, sa_column=Column(JSON))
    response_body: Any = Field(default=None, sa_column=Column(JSON))
    error_message: str | None = Field(default=None)
    redirected: bool = Field(default=False, nullable=False)
    redirect_count: int = Field(default=0, nullable=False)
    redirect_history: Any = Field(default=None, sa_column=Column(JSON))

    def to_pydantic_model(self):
        from models.job import Job as JobPydantic
        job_data = self.model_dump()
        return JobPydantic(**job_data)
