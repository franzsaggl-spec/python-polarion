from __future__ import annotations

from ..types.common import UserRef
from ..types.project import Project
from .common import maybe_list, require_dict


def parse_project(raw: dict) -> Project:
    d = require_dict(raw, context="project")
    return Project(
        id=str(d.get("id", "")),
        name=str(d.get("name", "")),
        tracker_prefix=d.get("trackerPrefix"),
    )


def parse_project_list(raw: object) -> list[Project]:
    return [parse_project(p) for p in maybe_list(raw) if isinstance(p, dict)]


def parse_user_ref(raw: object) -> UserRef:
    d = require_dict(raw, context="user")
    return UserRef(
        id=str(d.get("id") or d.get("name") or ""),
        uri=d.get("_uri") or d.get("uri"),
        name=d.get("name") or d.get("fullName"),
    )


def parse_user_ref_list(raw: object) -> list[UserRef]:
    return [parse_user_ref(u) for u in maybe_list(raw) if isinstance(u, dict)]
