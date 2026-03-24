from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .common import EnumRef


@dataclass(frozen=True)
class Plan:
    id: str
    uri: str
    name: str
    status: EnumRef | None
    start_date: date | None
    due_date: date | None


@dataclass
class PlanCreate:
    name: str
    plan_id: str
    template: str
    parent_id: str | None = None
