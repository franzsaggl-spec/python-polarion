from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    tracker_prefix: str | None = None
