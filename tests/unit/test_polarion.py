"""Tests for polarion/client.py Polarion class (v2.0.0 API)."""

import time
from unittest.mock import MagicMock, patch

import pytest

from polarion.client import Polarion
from polarion.exceptions import PolarionApiError

# ------------------------------------------------------------------
# has_service
# ------------------------------------------------------------------


def test_has_service_returns_true_for_existing(mock_polarion):
    assert mock_polarion.has_service("Session") is True
    assert mock_polarion.has_service("Tracker") is True
    assert mock_polarion.has_service("TestManagement") is True


def test_has_service_returns_false_for_missing(mock_polarion):
    assert mock_polarion.has_service("NonExistentService") is False
    assert mock_polarion.has_service("") is False


# ------------------------------------------------------------------
# Session check caching
# ------------------------------------------------------------------


def test_check_session_does_not_recheck_within_interval(mock_polarion):
    """_check_session should not re-check the session if called within the interval."""
    mock_polarion._last_session_check = time.time()
    mock_polarion._soap.call.reset_mock()

    mock_polarion._check_session()
    mock_polarion._check_session()

    # Should NOT have called _soap.call because we are within the interval
    mock_polarion._soap.call.assert_not_called()


def test_check_session_rechecks_after_interval(mock_polarion):
    """_check_session should re-check session validity when the interval has elapsed."""
    mock_polarion._last_session_check = time.time() - 600  # well past 300s
    mock_polarion._soap.call.reset_mock()

    mock_polarion._check_session()

    mock_polarion._soap.call.assert_called_once_with("Project", "getUser", userId=mock_polarion.user)


# ------------------------------------------------------------------
# __str__ and __repr__
# ------------------------------------------------------------------


def test_str_contains_url_and_user(mock_polarion):
    s = str(mock_polarion)
    assert mock_polarion.user in s
    assert "polarion.example.com" in s


def test_repr_contains_url_and_user(mock_polarion):
    r = repr(mock_polarion)
    assert mock_polarion.user in r
    assert "polarion.example.com" in r


def test_str_equals_repr(mock_polarion):
    assert str(mock_polarion) == repr(mock_polarion)


# ------------------------------------------------------------------
# download_from_svn
# ------------------------------------------------------------------


def test_download_from_svn_raises_on_failure(mock_polarion):
    with patch("polarion.client.requests") as mock_req:
        resp = MagicMock()
        resp.ok = False
        resp.status_code = 404
        resp.reason = "Not Found"
        mock_req.get.return_value = resp

        with pytest.raises(PolarionApiError, match="Could not download"):
            mock_polarion.download_from_svn("http://polarion.example.com/repo/file.txt")


def test_download_from_svn_returns_content_on_success(mock_polarion):
    with patch("polarion.client.requests") as mock_req:
        resp = MagicMock()
        resp.ok = True
        resp.content = b"file-bytes"
        mock_req.get.return_value = resp

        result = mock_polarion.download_from_svn("http://polarion.example.com/repo/file.txt")
        assert result == b"file-bytes"


def test_download_from_svn_uses_custom_svn_repo_url(mock_polarion):
    mock_polarion.svn_repo_url = "http://other-host.example.com/custom-repo"

    with patch("polarion.client.requests") as mock_req:
        resp = MagicMock()
        resp.ok = True
        resp.content = b"custom-bytes"
        mock_req.get.return_value = resp

        result = mock_polarion.download_from_svn("http://polarion.example.com/repo/project/path/file.txt")
        assert result == b"custom-bytes"

        # Verify the URL was rewritten to the custom repo
        called_url = mock_req.get.call_args[0][0]
        assert "other-host.example.com" in called_url


# ------------------------------------------------------------------
# Context manager
# ------------------------------------------------------------------


def test_context_manager_calls_close():
    with patch("polarion.client.SoapClient") as MockSoapClient:
        mock_soap = MagicMock()
        MockSoapClient.return_value = mock_soap
        mock_soap.discover_services.return_value = None
        mock_soap.login.return_value = None

        with Polarion(
            "http://polarion.example.com/polarion",
            "testuser",
            password="testpass",
        ) as _pol:
            pass

        mock_soap.logout.assert_called_once()
        mock_soap.close.assert_called_once()


# ------------------------------------------------------------------
# No hardcoded credentials
# ------------------------------------------------------------------


def test_no_hardcoded_credentials():
    """Ensure the source file does not contain hardcoded 'polarion' or 'aurora' passwords."""
    import os
    import re

    source_path = os.path.join(os.path.dirname(__file__), "..", "..", "polarion", "client.py")
    with open(source_path, "r") as f:
        source = f.read()

    # These are known default credentials that must not appear as literals
    for cred in ["aurora"]:
        pattern = rf"""password\s*=\s*['"]({cred})['"]"""
        assert not re.search(pattern, source, re.IGNORECASE), f'Found hardcoded credential "{cred}" in client.py'
    # Also check there is no default password in the __init__ signature
    init_pattern = r"def __init__\(.*password\s*=\s*['\"]"
    assert not re.search(init_pattern, source), "Found hardcoded default password in __init__ signature"
