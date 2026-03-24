from dataclasses import dataclass
from datetime import datetime

from .common import EnumRef


@dataclass(frozen=True)
class TestRun:
    id: str
    uri: str
    title: str
    is_template: bool
    status: EnumRef | None
    created_at: datetime | None


@dataclass(frozen=True)
class TestRecord:
    test_case_id: str
    result: str | None
    duration_ms: int | None
    comment: str | None


@dataclass
class TestRunCreate:
    id: str
    title: str
    template_id: str
