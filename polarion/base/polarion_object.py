"""Base class for all Polarion model objects."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from polarion.client import Polarion
    from polarion.project import Project


class PolarionObject:
    """Base class for Polarion model objects (Workitem, Document, Plan, etc.)."""

    _default_summary_fields: list[str] = []
    _field_accessors: dict[str, Any] = {}

    def __init__(
        self,
        polarion: Polarion,
        project: Project | None,
        id: str | None = None,
        uri: str | None = None,
    ) -> None:
        self._polarion = polarion
        self._project = project
        self._id = id
        self._uri = uri

    @property
    def uri(self) -> str | None:
        return self._uri

    @staticmethod
    def _populate_from_dict(target: Any, data: dict[str, Any], remap: dict[str, str] | None = None) -> None:
        """Populate target object attributes from a parsed SOAP response dict.

        :param target: Object to set attributes on
        :param data: Dict from parsed SOAP response
        :param remap: Optional field name remapping (soap_name -> python_name)
        """
        _skip = {"unresolvable", "uri"}
        for key, value in data.items():
            if key in _skip:
                continue
            name = remap.get(key, key) if remap else key
            setattr(target, name, value)

    @staticmethod
    def _build_changed_fields(
        current: dict[str, Any],
        original: dict[str, Any],
        skip: set[str] | None = None,
    ) -> dict[str, Any]:
        """Build a dict of changed fields by comparing current vs original values.

        :param current: Current field values
        :param original: Original field values (from last load)
        :param skip: Field names to skip
        :return: Dict of changed fields
        """
        changed: dict[str, Any] = {}
        for key, value in current.items():
            if skip and key in skip:
                continue
            if key in original and value != original[key]:
                changed[key] = value
        return changed

    @staticmethod
    def _truncate(text: str | None, max_len: int = 50) -> str:
        """Truncate text with ellipsis if longer than max_len."""
        if text is None:
            return ""
        if len(text) > max_len:
            return text[:max_len] + "..."
        return text

    def to_dict(self, fields: list[str] | None = None) -> dict[str, Any]:
        """Return a dictionary representation with selected fields.

        :param fields: Fields to include. Defaults to class-specific summary fields.
        :return: Dictionary with requested fields
        """
        if fields is None:
            fields = self._default_summary_fields

        result: dict[str, Any] = {}
        for f in fields:
            if f in self._field_accessors:
                result[f] = self._field_accessors[f](self)
            elif hasattr(self, f):
                value = getattr(self, f)
                if hasattr(value, "id") and not isinstance(value, (str, int, float, bool, date, datetime)):
                    result[f] = value.id
                else:
                    result[f] = value
        return result

    def _reload_from_polarion(self) -> None:
        raise NotImplementedError

    def save(self) -> None:
        raise NotImplementedError


class BatchSaveMixin:
    """Mixin providing context manager support for deferred save.

    Usage:
        with workitem.batch() as wi:
            wi.title = "New title"
            wi.description = TextContent("new desc")
        # save() called once on exit
    """

    _batch_save: bool = False

    def batch(self):
        """Return a context manager that defers save() until exit."""
        return _BatchContext(self)

    def __enter__(self):
        self._batch_save = True
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._batch_save = False
        if exc_type is None:
            self.save()


class _BatchContext:
    """Context manager for batch save operations."""

    def __init__(self, obj: Any) -> None:
        self._obj = obj

    def __enter__(self):
        self._obj._batch_save = True
        return self._obj

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._obj._batch_save = False
        if exc_type is None:
            self._obj.save()
