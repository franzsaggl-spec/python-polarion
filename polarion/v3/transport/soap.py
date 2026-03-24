"""SOAP transport implementation for v3."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import requests
from zeep import Client
from zeep.transports import Transport

from ..errors import AuthError, TransportError


@dataclass
class SoapTransport:
    url: str
    username: str
    password: str | None = None
    token: str | None = None
    verify_ssl: bool = True
    timeout: float = 30.0
    _clients: dict[str, Client] = field(default_factory=dict, init=False)
    _session: requests.Session = field(init=False)
    _authenticated: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self._session = requests.Session()
        self._session.verify = self.verify_ssl

    def _service_wsdl(self, service: str) -> str:
        base = self.url.rstrip("/")
        # Polarion SOAP endpoint convention
        return f"{base}/ws/services/{service}?wsdl"

    def _client(self, service: str) -> Client:
        existing = self._clients.get(service)
        if existing is not None:
            return existing

        transport = Transport(session=self._session, timeout=self.timeout)
        try:
            client = Client(wsdl=self._service_wsdl(service), transport=transport)
        except Exception as e:  # zeep has several exception types; normalize here.
            raise TransportError(f"Failed to initialize SOAP client for {service}: {e}") from e

        self._clients[service] = client
        return client

    def _authenticate(self) -> None:
        if self._authenticated:
            return

        if not self.password and not self.token:
            # Allow anonymous calls for environments configured that way.
            self._authenticated = True
            return

        session_client = self._client("Session")
        try:
            if self.token:
                # Token auth path (PAT/API token variants).
                # Many Polarion setups expose logInWithToken(user, token).
                session_client.service.logInWithToken(self.username, self.token)
            else:
                session_client.service.logIn(self.username, self.password)
        except Exception as e:
            raise AuthError(f"Failed to authenticate SOAP session for user {self.username}: {e}") from e

        self._authenticated = True

    def call(self, service: str, method: str, **kwargs: Any) -> Any:
        self._authenticate()
        client = self._client(service)
        fn = getattr(client.service, method, None)
        if fn is None:
            raise TransportError(f"SOAP method not found: {service}.{method}")
        try:
            return fn(**kwargs)
        except Exception as e:
            raise TransportError(f"SOAP call failed: {service}.{method}: {e}") from e

    def close(self) -> None:
        try:
            if self._authenticated:
                session_client = self._client("Session")
                end_session = getattr(session_client.service, "endSession", None)
                if end_session is not None:
                    end_session()
        except Exception:
            # Best-effort cleanup only.
            pass
        finally:
            self._session.close()
