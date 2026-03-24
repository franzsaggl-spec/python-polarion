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
        raw = self.transport.call("Project", "getUser", userId=user_id)
        if not isinstance(raw, dict):
            return User(id=user_id)
        return User(
            id=str(raw.get("id") or raw.get("name") or user_id),
            name=raw.get("name") or raw.get("fullName"),
            email=raw.get("email"),
        )

    def search(self, query: str | None = None, *, offset: int = 0, limit: int = 100) -> Page[User]:
        # Legacy API does not provide full user search endpoint.
        # For v3 initial implementation, this is intentionally empty.
        return Page(items=[], total=0, offset=offset, limit=limit, has_more=False)
