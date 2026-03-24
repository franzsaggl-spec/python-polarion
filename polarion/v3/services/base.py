from __future__ import annotations

from dataclasses import dataclass

from ..transport.soap import SoapTransport


@dataclass
class ServiceBase:
    transport: SoapTransport
