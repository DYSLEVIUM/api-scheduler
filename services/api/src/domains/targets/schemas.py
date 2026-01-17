from datetime import datetime
from urllib.parse import urljoin, urlparse
from uuid import UUID

from models.target import Target as TargetModel
from pydantic import BaseModel, Field, field_validator


class TargetRequest(TargetModel):
    url: str

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, url):
        if not isinstance(url, str):
            raise ValueError("URL must be a string")
        try:
            parsed_url = urlparse(urljoin(url, "/"))
            is_correct = (
                all([parsed_url.scheme, parsed_url.netloc, parsed_url.path])
                and len(parsed_url.netloc.split(".")) > 1
            )
            if not is_correct:
                raise ValueError("Invalid URL")
            return url
        except Exception as e:
            raise ValueError(f"Invalid URL: {e}")

    def to_model(self):
        from models.target import Target
        target_data = self.model_dump()
        target_data["url"] = urlparse(target_data["url"])
        return Target(**target_data)


class TargetResponse(TargetModel):
    id: UUID
    url: str
    created_at: datetime
    updated_at: datetime
