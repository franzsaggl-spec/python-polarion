"""Custom fields mixin for Polarion objects."""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

from polarion.base.polarion_object import PolarionObject
from polarion.exceptions import PolarionFieldError

if TYPE_CHECKING:
    from polarion.client import Polarion


class CustomFields(PolarionObject, ABC):
    """Mixin providing custom field get/set operations."""

    def __init__(
        self,
        polarion: Polarion,
        project: Any,
        id: str | None = None,
        uri: str | None = None,
    ) -> None:
        super().__init__(polarion, project, id, uri)
        self.customFields: list[dict[str, Any]] | None = None

    def is_custom_field_allowed(self, key: str) -> bool:
        raise NotImplementedError

    def set_custom_field(self, key: str, value: Any) -> None:
        """Set a custom field value.

        :param key: Custom field key
        :param value: Custom field value
        :raises PolarionFieldError: If the key is not allowed
        """
        if not self.is_custom_field_allowed(key):
            raise PolarionFieldError(f"key {key} is not allowed for this item")

        if self.customFields is None:
            self.customFields = []

        # Update existing or add new
        for cf in self.customFields:
            if cf.get("key") == key:
                cf["value"] = value
                return

        self.customFields.append({"key": key, "value": value})

    def get_custom_field(self, key: str) -> Any | None:
        """Get a custom field value.

        :param key: Custom field key
        :return: Custom field value, or None if not set
        """
        if self.customFields is not None:
            for cf in self.customFields:
                if cf.get("key") == key:
                    return cf.get("value")
        return None
