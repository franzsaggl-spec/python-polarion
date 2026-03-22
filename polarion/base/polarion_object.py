from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from polarion.polarion import Polarion
    from polarion.project import Project


class PolarionObject(object):
    def __init__(self, polarion: Polarion, project: Optional[Project], id: Optional[str] = None, uri: Optional[str] = None) -> None:
        self._polarion = polarion
        self._project = project
        self._id = id
        self._uri = uri

    def _reloadFromPolarion(self) -> None:
        raise NotImplementedError

    def save(self) -> None:
        raise NotImplementedError
