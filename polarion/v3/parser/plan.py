from __future__ import annotations

from ..types.common import EnumRef
from ..types.plan import Plan
from .common import maybe_list, require_dict


def parse_plan(raw: dict) -> Plan:
    d = require_dict(raw, context="plan")
    status_raw = d.get("status") if isinstance(d.get("status"), dict) else None
    status = None
    if status_raw is not None:
        status = EnumRef(
            id=str(status_raw.get("id", "")),
            uri=status_raw.get("_uri"),
            name=status_raw.get("name"),
        )

    return Plan(
        id=str(d.get("id", "")),
        uri=str(d.get("_uri") or d.get("uri") or ""),
        name=str(d.get("name") or d.get("title") or ""),
        status=status,
        start_date=None,
        due_date=None,
    )


def parse_plan_list(raw: object) -> list[Plan]:
    return [parse_plan(p) for p in maybe_list(raw) if isinstance(p, dict)]
