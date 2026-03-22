from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from .exceptions import PolarionNotFoundError, PolarionFieldError

if TYPE_CHECKING:
    from .polarion import Polarion
    from .project import Project

logger = logging.getLogger(__name__)


class Creator(ABC):
    test = 1

    @abstractmethod
    def createFromUri(self, polarion: Polarion, project: Any, uri: str) -> Any:
        pass


creator_list: dict[str, type[Creator]] = {}


def addCreator(type_name: str, creator: type[Creator]) -> None:
    creator_list[type_name] = creator


def createFromUri(polarion: Polarion, project: Any, uri: str) -> Any:
    type_name = _subterraUrl(uri)
    if type_name in creator_list:
        creator = creator_list[type_name]()
        return creator.createFromUri(polarion, project, uri)
    else:
        raise PolarionNotFoundError(f'type {type_name} not supported')


def _subterraUrl(uri: str) -> str:
    uri_parts = uri.split(':')
    if uri_parts[0] != 'subterra':
        raise PolarionFieldError(f'Not a subterra uri: {uri}')
    uri_type = re.findall(r"{(\w+)}", uri)
    if len(uri_type) >= 1:
        return uri_type[0].lower()
    else:
        raise PolarionFieldError(f'{uri} is not a valid polarion uri')
