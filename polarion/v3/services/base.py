from __future__ import annotations

from dataclasses import dataclass

from ..errors import NotFoundError
from ..transport.soap import SoapTransport


@dataclass
class ServiceBase:
    transport: SoapTransport

    @staticmethod
    def require_identifier(value: str | None, *, context: str) -> str:
        if not value:
            raise NotFoundError(f"{context} not found")
        return value
