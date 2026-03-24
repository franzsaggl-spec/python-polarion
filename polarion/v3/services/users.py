from __future__ import annotations

from dataclasses import dataclass

from ..types.common import Page
from .base import ServiceBase


@dataclass(frozen=True)
class User:
    id: str
    name: str | None = None
    email: str | None = None


class UsersService(ServiceBase):
    def get(self, user_id: str) -> User:
        raise NotImplementedError

    def search(self, query: str | None = None, *, offset: int = 0, limit: int = 100) -> Page[User]:
        raise NotImplementedError
