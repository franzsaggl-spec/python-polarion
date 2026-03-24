"""Tests for polarion.soap.client — SoapClient class."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest
import requests

from polarion.exceptions import PolarionApiError, PolarionAuthError, PolarionConnectionError
from polarion.soap.client import SoapClient

BASE_URL = "http://polarion.example.com/polarion"


@pytest.fixture()
def client() -> SoapClient:
    """Create a SoapClient instance without any network access."""
    return SoapClient(BASE_URL)


# ---------- discover_services ----------


class TestDiscoverServices:
    def test_static_populates_expected_services(self, client):
        client.discover_services(static=True)
        expected = ["Session", "Project", "Tracker", "Builder", "Planning", "TestManagement", "Security"]
        for svc in expected:
            assert client.has_service(svc), f"Missing service: {svc}"

    def test_static_builds_correct_urls(self, client):
        client.discover_services(static=True)
        assert client._services["Session"].endswith("/SessionWebService")
        assert client._services["Tracker"].endswith("/TrackerWebService")

    @patch.object(requests.Session, "get")
    def test_dynamic_parses_html(self, mock_get, client):
        mock_resp = MagicMock()
        mock_resp.text = (
            '<a href="SessionWebService">SessionWebService</a>'
            '<a href="TrackerWebService">TrackerWebService</a>'
            '<a href="CustomWebService">CustomWebService</a>'
        )
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        client.discover_services(static=False)
        assert client.has_service("Session")
        assert client.has_service("Tracker")
        assert client.has_service("Custom")

    @patch.object(requests.Session, "get")
    def test_dynamic_raises_connection_error_on_failure(self, mock_get, client):
        mock_get.side_effect = requests.ConnectionError("refused")
        with pytest.raises(PolarionConnectionError, match="Could not discover services"):
            client.discover_services(static=False)


# ---------- login ----------


class TestLogin:
    def test_login_raises_auth_error_on_generic_failure(self, client):
        client.discover_services(static=True)
        with patch.object(client, "_raw_call", side_effect=ValueError("bad")):
            with pytest.raises(PolarionAuthError, match="Could not log in for user"):
                client.login("admin", "password")

    def test_login_lets_connection_error_through(self, client):
        client.discover_services(static=True)
        with patch.object(client, "_raw_call", side_effect=PolarionConnectionError("no service")):
            with pytest.raises(PolarionConnectionError):
                client.login("admin", "password")

    def test_login_lets_api_error_through(self, client):
        client.discover_services(static=True)
        with patch.object(client, "_raw_call", side_effect=PolarionApiError("SOAP fault")):
            with pytest.raises(PolarionApiError):
                client.login("admin", "password")

    def test_login_success_extracts_session(self, client):
        client.discover_services(static=True)
        session_xml = (
            b'<?xml version="1.0"?>'
            b"<soapenv:Envelope "
            b'xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">'
            b"<soapenv:Header>"
            b'<sessionID xmlns="http://ws.polarion.com/session">sess123</sessionID>'
            b"</soapenv:Header>"
            b"<soapenv:Body><logInResponse/></soapenv:Body>"
            b"</soapenv:Envelope>"
        )
        with patch.object(client, "_raw_call", return_value=session_xml):
            client.login("admin", "password")
        assert client._session_header is not None
        assert client._session_header.text == "sess123"


# ---------- login_with_token ----------


class TestLoginWithToken:
    def test_raises_auth_error_on_generic_failure(self, client):
        client.discover_services(static=True)
        with patch.object(client, "_raw_call", side_effect=ValueError("bad")):
            with pytest.raises(PolarionAuthError, match="Could not log in with token"):
                client.login_with_token("admin", "my-token")

    def test_lets_connection_error_through(self, client):
        client.discover_services(static=True)
        with patch.object(client, "_raw_call", side_effect=PolarionConnectionError("no service")):
            with pytest.raises(PolarionConnectionError):
                client.login_with_token("admin", "my-token")

    def test_lets_api_error_through(self, client):
        client.discover_services(static=True)
        with patch.object(client, "_raw_call", side_effect=PolarionApiError("SOAP fault")):
            with pytest.raises(PolarionApiError):
                client.login_with_token("admin", "my-token")

    def test_correct_parameter_order(self, client):
        """tokenValue must come after additionalData to match WSDL order."""
        client.discover_services(static=True)
        captured_params = {}

        def capture_raw_call(service, method, params):
            captured_params.update(params)
            # Return valid session XML
            return (
                b'<?xml version="1.0"?>'
                b"<soapenv:Envelope "
                b'xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">'
                b"<soapenv:Header>"
                b'<sessionID xmlns="http://ws.polarion.com/session">s1</sessionID>'
                b"</soapenv:Header>"
                b"<soapenv:Body><logInWithTokenResponse/></soapenv:Body>"
                b"</soapenv:Envelope>"
            )

        with patch.object(client, "_raw_call", side_effect=capture_raw_call):
            client.login_with_token("admin", "my-token")

        assert captured_params["tokenType"] == "AccessToken"
        assert captured_params["additionalData"] == ""
        assert captured_params["tokenValue"] == "my-token"

        # Verify ordering: additionalData before tokenValue
        keys = list(captured_params.keys())
        assert keys.index("additionalData") < keys.index("tokenValue")


# ---------- logout ----------


class TestLogout:
    def test_logout_logs_on_failure(self, client, caplog):
        client.discover_services(static=True)
        with patch.object(client, "call", side_effect=Exception("session expired")):
            with caplog.at_level(logging.DEBUG):
                client.logout()
        assert "session expired" in caplog.text or "Logout failed" in caplog.text

    def test_logout_does_not_raise(self, client):
        client.discover_services(static=True)
        with patch.object(client, "call", side_effect=RuntimeError("boom")):
            # Should not raise
            client.logout()


# ---------- _extract_session ----------


class TestExtractSession:
    def test_raises_auth_error_when_no_session_id(self, client):
        xml = (
            b'<?xml version="1.0"?>'
            b"<soapenv:Envelope "
            b'xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">'
            b"<soapenv:Header/>"
            b"<soapenv:Body><logInResponse/></soapenv:Body>"
            b"</soapenv:Envelope>"
        )
        with pytest.raises(PolarionAuthError, match="No session ID"):
            client._extract_session(xml)

    def test_extracts_session_id(self, client):
        xml = (
            b'<?xml version="1.0"?>'
            b"<soapenv:Envelope "
            b'xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">'
            b"<soapenv:Header>"
            b'<sessionID xmlns="http://ws.polarion.com/session">abc</sessionID>'
            b"</soapenv:Header>"
            b"<soapenv:Body><logInResponse/></soapenv:Body>"
            b"</soapenv:Envelope>"
        )
        client._extract_session(xml)
        assert client._session_header is not None
        assert client._session_header.text == "abc"


# ---------- _raw_call ----------


class TestRawCall:
    def test_raises_connection_error_for_unknown_service(self, client):
        with pytest.raises(PolarionConnectionError, match="Service.*not available"):
            client._raw_call("NonExistent", "someMethod", {})
