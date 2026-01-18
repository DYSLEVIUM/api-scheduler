from abc import ABC
from uuid import UUID

from sqlmodel import Field

from db.mixins.timestamp import TimestampMixin
from db.mixins.uuid import UUIDMixin


class Schedule(UUIDMixin, TimestampMixin, ABC):
    name: str = Field(nullable=False)
    interval_seconds: int = Field(nullable=False)
    target_id: UUID = Field(foreign_key="targets.id",
                            nullable=False, index=True)
    paused: bool = Field(default=False, nullable=False)
    temporal_workflow_id: str | None = Field(default=None, nullable=True)

    def to_pydantic_model(self):
        raise NotImplementedError("to_pydantic_model must be implemented")

    def get_workflow_type(self) -> str:
        raise NotImplementedError("get_workflow_type must be implemented")


class IntervalSchedule(Schedule, table=True):
    __tablename__ = "interval_schedules"

    def to_pydantic_model(self):
        from models.schedule import \
            IntervalSchedule as IntervalSchedulePydantic
        schedule_data = self.model_dump()
        return IntervalSchedulePydantic(**schedule_data)

    def get_workflow_type(self) -> str:
        return "interval"


class WindowSchedule(Schedule, table=True):
    __tablename__ = "window_schedules"
    duration_seconds: int = Field(nullable=False)

    def to_pydantic_model(self):
        from models.schedule import WindowSchedule as WindowSchedulePydantic
        schedule_data = self.model_dump()
        return WindowSchedulePydantic(**schedule_data)

    def get_workflow_type(self) -> str:
        return "window"
