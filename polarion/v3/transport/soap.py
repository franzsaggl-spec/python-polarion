"""Transport abstraction for v3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SoapTransport:
    url: str
    username: str
    password: str | None = None
    token: str | None = None
    verify_ssl: bool = True
    timeout: float = 30.0

    def call(self, service: str, method: str, **kwargs: Any) -> Any:
        raise NotImplementedError

    def close(self) -> None:
        return None
