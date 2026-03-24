"""Factory pattern for creating Polarion objects from URIs."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from .exceptions import PolarionFieldError

if TYPE_CHECKING:
    from .client import Polarion


class Creator(ABC):
    """Abstract factory for creating objects from Polarion URIs."""

    @abstractmethod
    def create_from_uri(self, polarion: Polarion, project: Any, uri: str) -> Any:
        pass


_creator_registry: dict[str, type[Creator]] = {}


def register_creator(type_name: str, creator: type[Creator]) -> None:
    """Register a Creator for a given Polarion object type."""
    _creator_registry[type_name] = creator


def create_from_uri(polarion: Polarion, project: Any, uri: str) -> Any:
    """Create a Polarion object from its URI.

    :param polarion: Polarion client
    :param project: Project instance
    :param uri: Subterra URI
    :return: The appropriate Polarion object
    :raises PolarionFieldError: If the URI type is not supported
    """
    type_name = _parse_subterra_type(uri)
    if type_name in _creator_registry:
        creator = _creator_registry[type_name]()
        return creator.create_from_uri(polarion, project, uri)
    raise PolarionFieldError(f"type {type_name} not supported")


def _parse_subterra_type(uri: str) -> str:
    """Extract the object type from a subterra URI.

    :param uri: e.g. "subterra:data-service:objects:/default/project${WorkItem}WI-123"
    :return: e.g. "workitem"
    """
    uri_parts = uri.split(":")
    if uri_parts[0] != "subterra":
        raise PolarionFieldError(f"Not a subterra uri: {uri}")
    uri_type = re.findall(r"{(\w+)}", uri)
    if len(uri_type) >= 1:
        return uri_type[0].lower()
    raise PolarionFieldError(f"{uri} is not a valid polarion uri")
