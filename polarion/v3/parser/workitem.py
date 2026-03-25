from __future__ import annotations

from typing import Any

from ..types.common import AttachmentMeta, EnumRef, Link, UserRef
from ..types.workitem import WorkitemDetail, WorkitemSummary
from .common import maybe_list, parse_datetime, require_dict


def _enum_ref(raw: Any) -> EnumRef | None:
    if not isinstance(raw, dict):
        return None
    return EnumRef(id=str(raw.get("id", "")), uri=raw.get("_uri"), name=raw.get("name"))


def _user_ref(raw: Any) -> UserRef | None:
    if not isinstance(raw, dict):
        return None
    return UserRef(id=str(raw.get("id") or raw.get("name") or ""), uri=raw.get("_uri"), name=raw.get("name"))


def parse_workitem_summary(raw: dict[str, Any]) -> WorkitemSummary:
    d = require_dict(raw, context="workitem")
    return WorkitemSummary(
        id=str(d.get("id", "")),
        uri=str(d.get("_uri") or d.get("uri") or ""),
        title=d.get("title"),
        type=_enum_ref(d.get("type")),
        status=_enum_ref(d.get("status")),
        priority=_enum_ref(d.get("priority")),
    )


def parse_workitem_summary_list(raw: object) -> list[WorkitemSummary]:
    return [parse_workitem_summary(w) for w in maybe_list(raw) if isinstance(w, dict)]


def parse_workitem_detail(raw: dict[str, Any]) -> WorkitemDetail:
    d = require_dict(raw, context="workitem")
    summary = parse_workitem_summary(d)

    links: list[Link] = []
    for li in maybe_list(d.get("linkedWorkItems")):
        if isinstance(li, dict) and isinstance(li.get("workItemURI"), str):
            role = li.get("role", {})
            role_id = role.get("id") if isinstance(role, dict) else ""
            target_uri = li.get("workItemURI", "")
            links.append(Link(role=str(role_id or ""), target_id="", target_uri=str(target_uri)))

    attachments: list[AttachmentMeta] = []
    for a in maybe_list(d.get("attachments")):
        if isinstance(a, dict):
            attachments.append(
                AttachmentMeta(
                    id=str(a.get("id", "")),
                    file_name=str(a.get("fileName", "")),
                    title=a.get("title"),
                    url=a.get("url") or a.get("_uri"),
                )
            )

    author = _user_ref(d.get("author"))
    assignees = [_user_ref(u) for u in maybe_list(d.get("assignee"))]
    assignees = [u for u in assignees if u is not None]

    approvers: list[UserRef] = []
    for ap in maybe_list(d.get("approvals")):
        if isinstance(ap, dict):
            u = _user_ref(ap.get("user"))
            if u is not None:
                approvers.append(u)

    desc = d.get("description")
    desc_html = desc.get("content") if isinstance(desc, dict) else None

    return WorkitemDetail(
        **summary.__dict__,
        description_html=desc_html,
        author=author,
        assignees=assignees,
        approvers=approvers,
        links=links,
        attachments=attachments,
        custom_fields=d.get("customFields", {}) if isinstance(d.get("customFields"), dict) else {},
        created_at=parse_datetime(d.get("created"), context="workitem.created"),
        updated_at=parse_datetime(d.get("updated"), context="workitem.updated"),
    )
