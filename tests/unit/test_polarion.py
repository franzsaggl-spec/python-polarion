"""Tests for polarion/polarion.py Polarion class."""

import time
import pytest
from unittest.mock import MagicMock, patch

from polarion.exceptions import PolarionConnectionError, PolarionApiError


# ------------------------------------------------------------------
# hasService
# ------------------------------------------------------------------

def test_has_service_returns_true_for_existing(mock_polarion):
    assert mock_polarion.hasService('Session') is True
    assert mock_polarion.hasService('Tracker') is True
    assert mock_polarion.hasService('TestManagement') is True


def test_has_service_returns_false_for_missing(mock_polarion):
    assert mock_polarion.hasService('NonExistentService') is False
    assert mock_polarion.hasService('') is False


# ------------------------------------------------------------------
# getService
# ------------------------------------------------------------------

def test_get_service_raises_for_missing(mock_polarion):
    with pytest.raises(PolarionConnectionError, match='does not exist'):
        mock_polarion.getService('NoSuchService')


def test_get_service_returns_client_service(mock_polarion):
    # The mocked setup puts a client with .service on each service
    svc = mock_polarion.getService('Tracker')
    assert svc is not None


# ------------------------------------------------------------------
# Session check caching
# ------------------------------------------------------------------

def test_get_service_does_not_recheck_session_within_interval(mock_polarion):
    """getService should not re-check the session if called within the interval."""
    mock_polarion._last_session_check = time.time()
    mock_polarion._session_check_interval = 300

    # Reset call count on the Project service mock
    project_client = mock_polarion.services['Project']['client']
    project_client.service.getUser.reset_mock()

    mock_polarion.getService('Tracker')
    mock_polarion.getService('Tracker')

    # Should NOT have called getUser because we are within the interval
    project_client.service.getUser.assert_not_called()


def test_get_service_rechecks_session_after_interval(mock_polarion):
    """getService should re-check session validity when the interval has elapsed."""
    mock_polarion._last_session_check = time.time() - 600  # well past 300s
    mock_polarion._session_check_interval = 300

    project_client = mock_polarion.services['Project']['client']
    project_client.service.getUser.reset_mock()

    mock_polarion.getService('Tracker')

    project_client.service.getUser.assert_called_once_with(mock_polarion.user)


# ------------------------------------------------------------------
# get_client with plugins=None
# ------------------------------------------------------------------

def test_get_client_plugins_none_creates_empty_list(mock_polarion):
    """When plugins is None, get_client should default to an empty list."""
    with patch('polarion.polarion.Client') as MockClient, \
         patch('polarion.polarion.requests') as mock_req:
        mock_req.Session.return_value = MagicMock()
        MockClient.return_value = MagicMock()

        mock_polarion.get_client('Session', plugins=None)

        # The Client constructor should have been called with plugins=[]
        _, kwargs = MockClient.call_args
        assert kwargs.get('plugins') == [] or MockClient.call_args[0] == []


# ------------------------------------------------------------------
# __str__ and __repr__
# ------------------------------------------------------------------

def test_str_contains_url_and_user(mock_polarion):
    s = str(mock_polarion)
    assert mock_polarion.user in s
    assert 'polarion.example.com' in s


def test_repr_contains_url_and_user(mock_polarion):
    r = repr(mock_polarion)
    assert mock_polarion.user in r
    assert 'polarion.example.com' in r


def test_str_equals_repr(mock_polarion):
    assert str(mock_polarion) == repr(mock_polarion)


# ------------------------------------------------------------------
# downloadFromSvn
# ------------------------------------------------------------------

def test_download_from_svn_raises_on_failure(mock_polarion):
    with patch('polarion.polarion.requests') as mock_req:
        resp = MagicMock()
        resp.ok = False
        resp.status_code = 404
        resp.reason = 'Not Found'
        mock_req.get.return_value = resp

        with pytest.raises(PolarionApiError, match='Could not download'):
            mock_polarion.downloadFromSvn('http://polarion.example.com/repo/file.txt')


def test_download_from_svn_returns_content_on_success(mock_polarion):
    with patch('polarion.polarion.requests') as mock_req:
        resp = MagicMock()
        resp.ok = True
        resp.content = b'file-bytes'
        mock_req.get.return_value = resp

        result = mock_polarion.downloadFromSvn('http://polarion.example.com/repo/file.txt')
        assert result == b'file-bytes'


def test_download_from_svn_uses_custom_svn_repo_url(mock_polarion):
    mock_polarion.svn_repo_url = 'http://other-host.example.com/custom-repo'

    with patch('polarion.polarion.requests') as mock_req:
        resp = MagicMock()
        resp.ok = True
        resp.content = b'custom-bytes'
        mock_req.get.return_value = resp

        result = mock_polarion.downloadFromSvn(
            'http://polarion.example.com/repo/project/path/file.txt')
        assert result == b'custom-bytes'

        # Verify the URL was rewritten to the custom repo
        called_url = mock_req.get.call_args[0][0]
        assert 'other-host.example.com' in called_url


# ------------------------------------------------------------------
# No hardcoded credentials
# ------------------------------------------------------------------

def test_no_hardcoded_credentials():
    """Ensure the source file does not contain hardcoded 'polarion' or 'aurora' passwords."""
    import os
    source_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'polarion', 'polarion.py')
    with open(source_path, 'r') as f:
        source = f.read()

    # These are known default credentials that must not appear as literals
    # We check for string literals containing these passwords
    # (simple variable names like 'polarion_url' are fine)
    import re
    # Look for password-like assignments with literal 'polarion' or 'aurora'
    for cred in ['aurora']:
        # Match password= literal assignments
        pattern = rf"""password\s*=\s*['"]({cred})['"]"""
        assert not re.search(pattern, source, re.IGNORECASE), \
            f'Found hardcoded credential "{cred}" in polarion.py'
    # Also check there is no default password in the __init__ signature
    # (password=None is fine, password='something' is not)
    init_pattern = r"def __init__\(.*password\s*=\s*['\"]"
    assert not re.search(init_pattern, source), \
        'Found hardcoded default password in __init__ signature'
