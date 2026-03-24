"""Low-level SOAP client for Polarion web services.

Handles session management, SOAP envelope construction/parsing,
and HTTP transport using requests + lxml.
"""

from __future__ import annotations

import copy
import logging
import re
from typing import Any
from urllib.parse import urljoin

import requests
from lxml import etree

from ..exceptions import (
    PolarionApiError,
    PolarionAuthError,
    PolarionConnectionError,
)
from .envelope import NIL, build_envelope
from .parser import parse_response

logger = logging.getLogger(__name__)

_BASE_SERVICE_PATH = "ws/services"
_NS_SESSION = "http://ws.polarion.com/session"

SOAP_HEADERS = {
    "Content-Type": "text/xml; charset=utf-8",
    "SOAPAction": "",
}


class SoapClient:
    """Low-level SOAP client for Polarion web services.

    Wraps requests + lxml to build SOAP envelopes, send them to Polarion's
    WSDL endpoints, and parse responses.

    :param base_url: Polarion base URL (e.g. "https://polarion.example.com/polarion")
    :param verify_certificate: SSL certificate verification (bool or path to CA bundle)
    :param proxy: Optional proxy address ("ip:port")
    :param timeout: Request timeout in seconds
    """

    def __init__(
        self,
        base_url: str,
        verify_certificate: bool | str = True,
        proxy: str | None = None,
        timeout: int = 120,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._service_url = f"{self._base_url}/{_BASE_SERVICE_PATH}"
        self._timeout = timeout

        self._session = requests.Session()
        self._session.verify = verify_certificate
        if proxy is not None:
            self._session.proxies = {"http": proxy, "https": proxy}

        self._session_header: etree._Element | None = None
        self._cookie_jar: requests.cookies.RequestsCookieJar | None = None
        self._services: dict[str, str] = {}

    def discover_services(self, static: bool = False) -> None:
        """Discover available SOAP services.

        :param static: If True, use a static list instead of fetching from server
        """
        if static:
            default_services = [
                "Session", "Project", "Tracker", "Builder",
                "Planning", "TestManagement", "Security",
            ]
            for service in default_services:
                self._services[service] = f"{self._service_url}/{service}WebService"
        else:
            try:
                resp = self._session.get(self._service_url, timeout=self._timeout)
                resp.raise_for_status()
                services = re.findall(r"(\w+)WebService", resp.text)
                for service in services:
                    if service not in self._services:
                        self._services[service] = f"{self._service_url}/{service}WebService"
            except requests.RequestException as e:
                raise PolarionConnectionError(f"Could not discover services: {e}") from e

    def login(self, user: str, password: str) -> None:
        """Authenticate with username and password.

        :param user: Username
        :param password: Password
        :raises PolarionAuthError: If login fails
        """
        try:
            response_bytes = self._raw_call("Session", "logIn", {
                "userName": user,
                "password": password,
            })
            self._extract_session(response_bytes)
        except Exception as e:
            raise PolarionAuthError(f"Could not log in for user {user}") from e

    def login_with_token(self, user: str, token: str) -> None:
        """Authenticate with a personal access token.

        :param user: Username
        :param token: Access token
        :raises PolarionAuthError: If login fails
        """
        try:
            response_bytes = self._raw_call("Session", "logInWithToken", {
                "tokenType": "AccessToken",
                "tokenValue": token,
                "additionalData": "",
            })
            self._extract_session(response_bytes)
        except Exception as e:
            raise PolarionAuthError(f"Could not log in with token for user {user}") from e

    def logout(self) -> None:
        """End the current session."""
        try:
            self.call("Session", "endSession")
        except Exception:
            pass

    def call(self, service: str, method: str, **params: Any) -> Any:
        """Make a SOAP call and return parsed response.

        :param service: Service name (e.g. "Tracker")
        :param method: Method name (e.g. "getWorkItemById")
        :param params: Method parameters
        :return: Parsed response (dict, list, str, or None)
        :raises PolarionConnectionError: If service not found
        :raises PolarionApiError: If SOAP call fails
        """
        response_bytes = self._raw_call(service, method, params)
        return parse_response(response_bytes)

    def has_service(self, name: str) -> bool:
        """Check if a service is available."""
        return name in self._services

    def _raw_call(self, service: str, method: str, params: dict[str, Any]) -> bytes:
        """Send a SOAP request and return raw response bytes."""
        if service not in self._services:
            raise PolarionConnectionError(f"Service {service} not available")

        url = self._services[service]
        envelope = build_envelope(service, method, params, self._session_header)

        try:
            response = self._session.post(
                url,
                data=envelope,
                headers=SOAP_HEADERS,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise PolarionApiError(f"SOAP call {service}.{method} failed: {e}") from e

        return response.content

    def _extract_session(self, response_bytes: bytes) -> None:
        """Extract session ID from login response and store cookies."""
        root = etree.fromstring(response_bytes)
        session_id = root.find(f".//{{{_NS_SESSION}}}sessionID")
        if session_id is not None:
            self._session_header = copy.deepcopy(session_id)
            self._cookie_jar = self._session.cookies.copy()
        else:
            raise PolarionAuthError("No session ID returned by login")

    def close(self) -> None:
        """Close the HTTP session."""
        self._session.close()
