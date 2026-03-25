from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from ..errors import NotFoundError, ValidationError
from ..transport.soap import SoapTransport
from ..types.common import Page

T = TypeVar("T")


@dataclass
class ServiceBase:
    transport: SoapTransport

    @staticmethod
    def require_identifier(value: str | None, *, context: str) -> str:
        if not value:
            raise NotFoundError(f"{context} not found")
        return value

    @staticmethod
    def paginate(items: list[T], *, offset: int, limit: int) -> Page[T]:
        if offset < 0:
            raise ValidationError("offset must be >= 0")
        if limit <= 0:
            raise ValidationError("limit must be > 0")

        sliced = items[offset : offset + limit]
        return Page(
            items=sliced,
            total=len(items),
            offset=offset,
            limit=limit,
            has_more=offset + len(sliced) < len(items),
        )
