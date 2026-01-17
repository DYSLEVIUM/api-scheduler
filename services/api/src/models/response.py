from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class HTTPResponse(BaseModel, Generic[T]):
    success: bool
    error: Optional[Any] = None
    status_code: int
    message: str
    data: Optional[T] = None
