"""Python dataclasses wrapping Polarion SOAP types.

These replace the raw zeep types that were previously exposed to users.
Users interact with these clean Python objects instead of SOAP internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class TextContent:
    """Rich text content (descriptions, comments, etc.)."""

    content: str
    content_type: str = "text/html"
    content_lossy: bool = False

    def to_soap(self) -> dict[str, Any]:
        return {
            "type": self.content_type,
            "content": self.content,
            "contentLossy": self.content_lossy,
        }

    @classmethod
    def from_soap(cls, data: dict[str, Any] | None) -> TextContent | None:
        if data is None:
            return None
        return cls(
            content=data.get("content", ""),
            content_type=data.get("type", "text/html"),
            content_lossy=data.get("contentLossy", False),
        )


@dataclass
class EnumOption:
    """An enumeration option (status, type, resolution, etc.)."""

    id: str
    name: str | None = None

    def to_soap(self) -> dict[str, Any]:
        return {"id": self.id}

    @classmethod
    def from_soap(cls, data: dict[str, Any] | str | None) -> EnumOption | None:
        if data is None:
            return None
        if isinstance(data, str):
            return cls(id=data)
        return cls(
            id=data.get("id", ""),
            name=data.get("name"),
        )


@dataclass
class LinkedItem:
    """A link between two work items."""

    role: str
    workitem_uri: str
    suspect: bool = False

    @classmethod
    def from_soap(cls, data: dict[str, Any] | None) -> LinkedItem | None:
        if data is None:
            return None
        role_data = data.get("role", {})
        role_id = role_data.get("id", "") if isinstance(role_data, dict) else str(role_data)
        return cls(
            role=role_id,
            workitem_uri=data.get("workItemURI", ""),
            suspect=data.get("suspect", False),
        )


@dataclass
class Approval:
    """A work item approval."""

    user_id: str
    status: str | None = None

    @classmethod
    def from_soap(cls, data: dict[str, Any] | None) -> Approval | None:
        if data is None:
            return None
        user_data = data.get("user", {})
        user_id = user_data.get("id", "") if isinstance(user_data, dict) else str(user_data)
        status_data = data.get("status", {})
        status = status_data.get("id") if isinstance(status_data, dict) else status_data
        return cls(user_id=user_id, status=status)


@dataclass
class CustomFieldValue:
    """A custom field key-value pair."""

    key: str
    value: Any

    def to_soap(self) -> dict[str, Any]:
        return {"key": self.key, "value": self.value}

    @classmethod
    def from_soap(cls, data: dict[str, Any] | None) -> CustomFieldValue | None:
        if data is None:
            return None
        return cls(
            key=data.get("key", ""),
            value=data.get("value"),
        )


@dataclass
class AttachmentInfo:
    """Metadata about an attachment."""

    id: str
    file_name: str
    title: str | None = None
    url: str | None = None
    length: int | None = None

    @classmethod
    def from_soap(cls, data: dict[str, Any] | None) -> AttachmentInfo | None:
        if data is None:
            return None
        return cls(
            id=data.get("id", ""),
            file_name=data.get("fileName", ""),
            title=data.get("title"),
            url=data.get("url"),
            length=data.get("length"),
        )


@dataclass
class HyperlinkInfo:
    """A hyperlink attached to a work item."""

    uri: str
    role: str

    @classmethod
    def from_soap(cls, data: dict[str, Any] | None) -> HyperlinkInfo | None:
        if data is None:
            return None
        role_data = data.get("role", {})
        role_id = role_data.get("id", "") if isinstance(role_data, dict) else str(role_data)
        return cls(uri=data.get("uri", ""), role=role_id)


@dataclass
class TestStep:
    """A single test step with column values."""

    values: dict[str, str]

    @classmethod
    def from_parsed(cls, columns: list[str], values: list[str]) -> TestStep:
        return cls(values=dict(zip(columns, values)))


@dataclass
class TestStepResult:
    """Result of a single test step execution."""

    result: str | None = None
    comment: str | None = None

    @classmethod
    def from_soap(cls, data: dict[str, Any] | None) -> TestStepResult | None:
        if data is None:
            return None
        result_data = data.get("result", {})
        result_id = result_data.get("id") if isinstance(result_data, dict) else result_data
        comment_data = data.get("comment", {})
        comment = comment_data.get("content") if isinstance(comment_data, dict) else comment_data
        return cls(result=result_id, comment=comment)


@dataclass
class PdfProperties:
    """PDF export properties."""

    paper_size: str = "A4"
    orientation: str = "Portrait"
    fit_to_page_width: bool = True
    mark_optional_fields: bool = True
    generate_bookmarks: bool = True
    update_linked_items: bool = True

    def to_soap(self) -> dict[str, Any]:
        return {
            "paperSize": self.paper_size,
            "orientation": self.orientation,
            "fitToPageWidth": self.fit_to_page_width,
            "markOptionalFields": self.mark_optional_fields,
            "generateBookmarks": self.generate_bookmarks,
            "updateLinkedItems": self.update_linked_items,
        }
