from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from polarion.polarion import Polarion
    from polarion.project import Project


class PolarionObject:
    def __init__(self, polarion: Polarion, project: Optional[Project], id: Optional[str] = None, uri: Optional[str] = None) -> None:
        self._polarion = polarion
        self._project = project
        self._id = id
        self._uri = uri

    @staticmethod
    def _populate_attrs(target: Any, polarion_obj: Any, remap: Optional[dict[str, str]] = None) -> None:
        """Populate target object attributes from a zeep compound object."""
        for attr, value in polarion_obj.__dict__.items():
            for key in value:
                name = remap.get(key, key) if remap else key
                setattr(target, name, value[key])

    @staticmethod
    def _build_update_dict(obj: Any, polarion_obj: Any, original_obj: Any, skip: Optional[set[str]] = None) -> dict[str, Any]:
        """Build a dict of changed attributes by diffing current vs original state."""
        updated: dict[str, Any] = {}
        for attr, value in polarion_obj.__dict__.items():
            for key in value:
                if skip and key in skip:
                    continue
                if getattr(obj, key) != getattr(original_obj, key):
                    updated[key] = getattr(obj, key)
        return updated

    def _reloadFromPolarion(self) -> None:
        raise NotImplementedError

    def save(self) -> None:
        raise NotImplementedError


class PostponeSaveMixin:
    """Mixin providing context manager support for deferred save."""
    _postpone_save: bool = False

    def __enter__(self):
        self._postpone_save = True
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._postpone_save = False
        self.save()
