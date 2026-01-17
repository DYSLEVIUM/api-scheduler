from typing import Any
from uuid import UUID

from db.mixins.timestamp import TimestampMixin
from db.mixins.uuid import UUIDMixin
from enums.http_methods import HTTPMethods
from sqlalchemy import JSON, Column
from sqlmodel import Field


class Target(UUIDMixin, TimestampMixin, table=True):
    __tablename__ = "targets"

    name: str = Field(index=True)
    url_id: UUID = Field(foreign_key="urls.id", nullable=False)
    method: HTTPMethods = Field(nullable=False)
    headers: Any = Field(default=None, sa_column=Column(JSON))
    body: Any = Field(default=None, sa_column=Column(JSON))

    def to_pydantic_model(self, url_string: str):
        from urllib.parse import urlparse

        from models.target import Target as TargetPydantic
        target_data = self.model_dump()
        target_data["url"] = urlparse(url_string)
        return TargetPydantic(**target_data)
