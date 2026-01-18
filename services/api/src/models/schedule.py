from __future__ import annotations

from abc import ABC
from datetime import datetime
from typing import TYPE_CHECKING, override
from uuid import UUID

from pydantic import BaseModel

from db.models.schedule import IntervalSchedule as IntervalScheduleModel
from db.models.schedule import WindowSchedule as WindowScheduleModel

if TYPE_CHECKING:
    from domains.schedules.schemas import (IntervalScheduleResponse,
                                           WindowScheduleResponse)


class Schedule(BaseModel, ABC):
    id: UUID | None = None
    name: str | None = None
    target_id: UUID | None = None
    interval_seconds: int | None = None
    paused: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_db_model(self):
        raise NotImplementedError("to_db_model must be implemented")

    def to_response(self):
        raise NotImplementedError("to_response must be implemented")


class IntervalSchedule(Schedule):
    @override
    def to_db_model(self):
        schedule_data = self.model_dump(exclude_none=True)
        return IntervalScheduleModel(**schedule_data)

    @override
    def to_response(self):
        from domains.schedules.schemas import IntervalScheduleResponse
        schedule_data = self.model_dump()
        return IntervalScheduleResponse(**schedule_data)


class WindowSchedule(Schedule):
    duration_seconds: int

    @override
    def to_db_model(self):
        schedule_data = self.model_dump(exclude_none=True)
        return WindowScheduleModel(**schedule_data)

    @override
    def to_response(self):
        from domains.schedules.schemas import WindowScheduleResponse
        schedule_data = self.model_dump()
        return WindowScheduleResponse(**schedule_data)
