from __future__ import annotations

from ..types.testrun import TestRun
from .common import maybe_list, require_dict


def parse_testrun(raw: dict) -> TestRun:
    d = require_dict(raw, context="testrun")
    return TestRun(
        id=str(d.get("id", "")),
        uri=str(d.get("_uri") or d.get("uri") or ""),
        title=str(d.get("title") or d.get("name") or ""),
        is_template=bool(d.get("isTemplate", False)),
        status=d.get("status") if isinstance(d.get("status"), dict) else None,
        created_at=None,
    )


def parse_testrun_list(raw: object) -> list[TestRun]:
    return [parse_testrun(t) for t in maybe_list(raw) if isinstance(t, dict)]
