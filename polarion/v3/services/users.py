from __future__ import annotations

from dataclasses import dataclass

from ..errors import NotFoundError
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
            raise NotFoundError(f"user {user_id} not found")
        user = User(
            id=str(raw.get("id") or raw.get("name") or ""),
            name=raw.get("name") or raw.get("fullName"),
            email=raw.get("email"),
        )
        self.require_identifier(user.id, context=f"user {user_id}")
        return user

    def search(self, query: str | None = None, *, offset: int = 0, limit: int = 100) -> Page[User]:
        # Legacy API does not provide full user search endpoint.
        # For v3 initial implementation, this is intentionally empty.
        return self.paginate([], offset=offset, limit=limit)
