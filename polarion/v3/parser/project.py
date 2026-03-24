from __future__ import annotations

from ..types.project import Project
from .common import require_dict


def parse_project(raw: dict) -> Project:
    d = require_dict(raw, context="project")
    return Project(
        id=str(d.get("id", "")),
        name=str(d.get("name", "")),
        tracker_prefix=d.get("trackerPrefix"),
    )
