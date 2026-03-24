"""Parser common helpers for v3."""

from __future__ import annotations

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
