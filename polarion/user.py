"""Polarion User model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base.polarion_object import PolarionObject
from .exceptions import PolarionNotFoundError
from .factory import Creator

if TYPE_CHECKING:
    from .client import Polarion


class User(PolarionObject):
    """A Polarion user.

    :param polarion: Polarion client instance
    :param polarion_record: User data from SOAP response
    :param uri: User URI for loading from server
    """

    id: str
    name: str
    email: str | None = None
    description: str | None = None
    avatarUrl: str | None = None
    disabledNotifications: bool | None = None

    def __init__(
        self,
        polarion: Polarion,
        polarion_record: dict[str, Any] | None = None,
        uri: str | None = None,
    ) -> None:
        super().__init__(polarion, None, None, uri)
        self._polarion_record = polarion_record

        if uri is not None:
            self._polarion_record = self._polarion._soap.call(
                "Project", "getUserByUri", uri=self._uri
            )

        if self._polarion_record is not None and isinstance(self._polarion_record, dict):
            if self._polarion_record.get("unresolvable"):
                raise PolarionNotFoundError("User not found")
            self._populate_from_dict(self, self._polarion_record)
        else:
            raise PolarionNotFoundError("User not retrieved from Polarion")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id

    def __repr__(self) -> str:
        return f"{self.name} ({self.id})"

    __str__ = __repr__


class UserCreator(Creator):
    def create_from_uri(self, polarion: Polarion, project: Any, uri: str) -> User:
        return User(polarion, None, uri)
