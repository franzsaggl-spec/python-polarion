from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .common import AttachmentMeta, EnumRef, Link, UserRef


@dataclass(frozen=True)
class WorkitemSummary:
    id: str
    uri: str
    title: str | None
    type: EnumRef | None
    status: EnumRef | None
    priority: EnumRef | None


@dataclass(frozen=True)
class WorkitemDetail(WorkitemSummary):
    description_html: str | None
    author: UserRef | None
    assignees: list[UserRef]
    approvers: list[UserRef]
    links: list[Link]
    attachments: list[AttachmentMeta]
    custom_fields: dict[str, Any]
    created_at: datetime | None
    updated_at: datetime | None


@dataclass
class WorkitemCreate:
    type_id: str
    title: str
    description_html: str | None = None
    fields: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkitemUpdate:
    title: str | None = None
    description_html: str | None = None
    status_id: str | None = None
    resolution_id: str | None = None
    severity_id: str | None = None
    priority_id: str | None = None
    assignee_ids: list[str] | None = None
    fields: dict[str, Any] = field(default_factory=dict)
