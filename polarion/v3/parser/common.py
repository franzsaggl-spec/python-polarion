"""Parser common helpers for v3."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..errors import ParsingError


def require_dict(value: Any, *, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ParsingError(f"Expected dict for {context}, got {type(value).__name__}")
    return value


def maybe_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def parse_datetime(value: Any, *, context: str) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        raise ParsingError(f"Expected datetime string for {context}, got {type(value).__name__}")

    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as e:
        raise ParsingError(f"Invalid datetime for {context}: {value}") from e
