from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declared_attr
from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel):
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(),
        description="Database timestamp when the record was created.",
    )

    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(),
        nullable=False,
        sa_column_kwargs={
            "onupdate": lambda: datetime.now(),
        },
    )
