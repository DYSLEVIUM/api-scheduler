from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from urllib.parse import ParseResult, urlparse, urlunparse
from uuid import UUID

from pydantic import BaseModel, Field

from db.models.target import Target as TargetModel
from enums.http_methods import HTTPMethods

if TYPE_CHECKING:
    from domains.targets.schemas import TargetResponse


class Target(BaseModel):
    id: UUID | None = None
    name: str = Field(..., min_length=5)
    url: ParseResult | str
    method: HTTPMethods
    headers: dict[str, str]
    body: dict[str, str] | None = None
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    retry_count: int = Field(default=0, ge=0, le=10)
    retry_delay_seconds: int = Field(default=1, ge=0, le=60)
    follow_redirects: bool = Field(default=True)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_db_model(self):
        target_data = self.model_dump(exclude={"url", "id"})
        return TargetModel(**target_data)

    def get_url_parse_result(self) -> ParseResult:
        if isinstance(self.url, ParseResult):
            return self.url
        return urlparse(self.url)

    def to_response(self):
        from domains.targets.schemas import TargetResponse

        # Convert URL to string before dumping to avoid ParseResult serialization issues
        url_value = self.url
        if isinstance(url_value, ParseResult):
            url_string = urlunparse(url_value)
        else:
            url_string = str(url_value) if url_value is not None else ""

        target_data = self.model_dump(exclude={"url"})
        target_data["url"] = url_string
        return TargetResponse(**target_data)
