from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from .exceptions import PolarionNotFoundError
from .factory import Creator

if TYPE_CHECKING:
    from .polarion import Polarion


class User(object):
    """
    A polarion user

    :param polarion: Polarion client object
    :param polarion_record: The user record

    """

    def __init__(self, polarion: Polarion, polarion_record: Optional[Any] = None, uri: Optional[str] = None) -> None:
        self._polarion = polarion
        self._polarion_record = polarion_record
        self._uri = uri

        if uri is not None:
            service = self._polarion.getService('Project')
            self._polarion_record = service.getUserByUri(self._uri)

        if self._polarion_record is not None and not self._polarion_record.unresolvable:
            # parse all polarion attributes to this class
            for attr, value in self._polarion_record.__dict__.items():
                for key in value:
                    setattr(self, key, value[key])
        else:
            raise PolarionNotFoundError('User not retrieved from Polarion')

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id

    def __repr__(self) -> str:
        return f'{self.name} ({self.id})'

    __str__ = __repr__


class UserCreator(Creator):
    def createFromUri(self, polarion: Polarion, project: Any, uri: str) -> User:
        return User(polarion, None, uri)
