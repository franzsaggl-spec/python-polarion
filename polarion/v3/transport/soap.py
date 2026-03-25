"""SOAP transport implementation for v3."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import requests
from zeep import Client
from zeep.exceptions import Error as ZeepError
from zeep.exceptions import Fault as ZeepFault
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
    max_retries: int = 2
    retry_backoff_seconds: float = 0.2

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
        except (ZeepError, requests.RequestException, OSError) as e:
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
        except (ZeepFault, ZeepError, requests.RequestException, OSError) as e:
            raise AuthError(f"Failed to authenticate SOAP session for user {self.username}: {e}") from e

        self._authenticated = True

    def call(self, service: str, method: str, **kwargs: Any) -> Any:
        self._authenticate()
        client = self._client(service)
        fn = getattr(client.service, method, None)
        if fn is None:
            raise TransportError(f"SOAP method not found: {service}.{method}")

        kwargs.pop("_timeout", None)  # reserved for future per-call transport override

        attempts = self.max_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                return fn(**kwargs)
            except ZeepFault as e:
                # SOAP-level faults are not transient; fail fast.
                raise TransportError(f"SOAP call failed: {service}.{method}: {e}") from e
            except (requests.Timeout, requests.ConnectionError, OSError) as e:
                if attempt >= attempts:
                    raise TransportError(f"SOAP call failed after retries: {service}.{method}: {e}") from e
                time.sleep(self.retry_backoff_seconds * attempt)
            except ZeepError as e:
                # Some Zeep transport/parsing errors are transient-ish in practice.
                if attempt >= attempts:
                    raise TransportError(f"SOAP call failed after retries: {service}.{method}: {e}") from e
                time.sleep(self.retry_backoff_seconds * attempt)

        raise TransportError(f"SOAP call failed: {service}.{method}")

    def call_with_fallback(self, service: str, methods: list[str], **kwargs: Any) -> Any:
        """Try multiple SOAP methods in order and return first successful response."""
        errors: list[str] = []
        for method in methods:
            try:
                return self.call(service, method, **kwargs)
            except TransportError as e:
                errors.append(f"{method}: {e}")

        raise TransportError(f"SOAP call failed for all fallback methods on {service}: " + "; ".join(errors))

    def supports_method(self, service: str, method: str) -> bool:
        """Check whether a SOAP method exists on a service without calling it."""
        client = self._client(service)
        return getattr(client.service, method, None) is not None

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
