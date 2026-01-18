from __future__ import annotations

from datetime import datetime
from typing import Union, override
from uuid import UUID

from pydantic import BaseModel, Field

from models.schedule import IntervalSchedule, WindowSchedule


class ScheduleRequestBase(BaseModel):
    name: str = Field(..., description="Name of the schedule")
    target_id: UUID
    interval_seconds: int = Field(
        ..., gt=0, description="Interval in seconds between runs"
    )

    def to_model(self):
        raise NotImplementedError("ScheduleRequest must be subclassed")


class IntervalScheduleRequest(ScheduleRequestBase):
    @override
    def to_model(self) -> IntervalSchedule:
        return IntervalSchedule(**self.model_dump())


class WindowScheduleRequest(ScheduleRequestBase):
    duration_seconds: int = Field(
        ..., gt=0, description="Duration in seconds for the window"
    )

    @override
    def to_model(self) -> WindowSchedule:
        return WindowSchedule(**self.model_dump())


ScheduleRequest = Union[IntervalScheduleRequest, WindowScheduleRequest]


class IntervalScheduleResponse(BaseModel):
    id: UUID
    name: str
    target_id: UUID
    interval_seconds: int
    paused: bool
    created_at: datetime
    updated_at: datetime


class WindowScheduleResponse(BaseModel):
    id: UUID
    name: str
    target_id: UUID
    interval_seconds: int
    duration_seconds: int
    paused: bool
    created_at: datetime
    updated_at: datetime


ScheduleResponse = Union[IntervalScheduleResponse, WindowScheduleResponse]
