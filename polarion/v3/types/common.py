from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Ref:
    id: str
    uri: str | None = None
    name: str | None = None


@dataclass(frozen=True)
class UserRef(Ref):
    pass


@dataclass(frozen=True)
class EnumRef(Ref):
    pass


@dataclass(frozen=True)
class Link:
    role: str
    target_id: str
    target_uri: str


@dataclass(frozen=True)
class AttachmentMeta:
    id: str
    file_name: str
    title: str | None
    url: str | None


@dataclass(frozen=True)
class Page(Generic[T]):
    items: list[T]
    total: int | None
    offset: int
    limit: int
    has_more: bool
