from datetime import datetime
from typing import Any
from uuid import UUID

from db.mixins.timestamp import TimestampMixin
from db.mixins.uuid import UUIDMixin
from enums.job_status import JobStatus
from sqlalchemy import JSON, Column
from sqlmodel import Field

from .job import JobStatusEnum


class Attempt(UUIDMixin, TimestampMixin, table=True):
    __tablename__ = "attempts"

    job_id: UUID = Field(nullable=False, index=True, foreign_key="jobs.id")
    attempt_number: int = Field(nullable=False)
    started_at: datetime = Field(nullable=False)
    status: JobStatus = Field(sa_column=Column(JobStatusEnum(), nullable=False))
    status_code: int | None = Field(default=None)
    latency_ms: float | None = Field(default=None)
    response_size_bytes: int | None = Field(default=None)
    response_headers: Any = Field(default=None, sa_column=Column(JSON))
    response_body: Any = Field(default=None, sa_column=Column(JSON))
    error_message: str | None = Field(default=None)

    def to_pydantic_model(self):
        from models.attempt import Attempt as AttemptPydantic
        return AttemptPydantic(**self.model_dump())
