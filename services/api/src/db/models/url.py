from urllib.parse import ParseResult, urlunparse

from db.mixins.timestamp import TimestampMixin
from db.mixins.uuid import UUIDMixin
from sqlmodel import Field


class URL(UUIDMixin, TimestampMixin, table=True):
    __tablename__ = "urls"

    scheme: str = Field(default="https", nullable=False)
    netloc: str = Field(nullable=False, index=True)
    path: str = Field(nullable=False)
    params: str | None = Field(default=None, nullable=True)
    query: str | None = Field(default=None, nullable=True)
    fragment: str | None = Field(default=None, nullable=True)

    def get_parsed_url(self) -> ParseResult:
        return ParseResult(
            self.scheme,
            self.netloc,
            self.path,
            self.params,
            self.query,
            self.fragment,
        )

    def get_url_string(self) -> str:
        return urlunparse(self.get_parsed_url())
