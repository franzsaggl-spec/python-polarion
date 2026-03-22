"""Tests for Testrun with mocked SOAP layer."""

import copy
import pytest
from unittest.mock import MagicMock, patch

from polarion.testrun import Testrun
from polarion.exceptions import PolarionNotFoundError, PolarionFieldError

# Local import of the shared zeep mock helper from conftest
from tests.unit.conftest import _zeep_object


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_testrun_data():
    """A sample testrun zeep-style object as returned by the TestManagement service."""
    test_record = _zeep_object({
        'testCaseURI': 'subterra:data-service:objects:/default/test_project${WorkItem}TC-001',
        'defectURI': None,
        'result': None,
        'comment': None,
        'executed': None,
        'executedByURI': None,
        'duration': None,
        'testStepResults': None,
        'attachments': None,
    })

    records_array = MagicMock()
    records_array.TestRecord = [test_record]

    return _zeep_object({
        'id': 'TR-001',
        'title': 'Test Run 1',
        'uri': 'subterra:data-service:objects:/default/test_project${TestRun}TR-001',
        'created': '2024-01-01',
        'updated': '2024-01-02',
        'records': records_array,
        'attachments': None,
        'customFields': None,
        'projectURI': None,
        'type': None,
        'status': None,
        'finishedOn': None,
        'isTemplate': False,
        'document': None,
        'comments': None,
        'author': None,
        'idPrefix': None,
        'groupId': None,
        'homePageContent': None,
        'keepInHistory': None,
        'selectTestCasesBy': None,
        'templateURI': None,
        'query': None,
        'useReportFromTemplate': None,
    })


def _make_testrun(mock_polarion, mock_testrun_data):
    """Build a Testrun from mocked data without hitting SOAP."""
    test_mgmt_service = MagicMock()
    test_mgmt_service.getTestRunByUri.return_value = mock_testrun_data

    original_get_service = mock_polarion.getService

    def _get_service(name):
        if name == 'TestManagement':
            return test_mgmt_service
        return original_get_service(name)

    with patch.object(mock_polarion, 'getService', side_effect=_get_service):
        tr = Testrun(mock_polarion, polarion_test_run=mock_testrun_data)

    mock_polarion.getService = MagicMock(side_effect=_get_service)
    return tr


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------

def test_testrun_creation_from_data(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    assert tr.id == 'TR-001'
    assert tr.title == 'Test Run 1'


def test_testrun_creation_from_uri(mock_polarion, mock_testrun_data):
    test_mgmt_service = MagicMock()
    test_mgmt_service.getTestRunByUri.return_value = mock_testrun_data

    def _get_service(name):
        if name == 'TestManagement':
            return test_mgmt_service
        return MagicMock()

    with patch.object(mock_polarion, 'getService', side_effect=_get_service):
        tr = Testrun(mock_polarion, uri=mock_testrun_data.uri)

    assert tr.id == 'TR-001'
    test_mgmt_service.getTestRunByUri.assert_called_once_with(mock_testrun_data.uri)


def test_testrun_neither_uri_nor_data_raises_field_error(mock_polarion):
    with pytest.raises(PolarionFieldError):
        Testrun(mock_polarion)


def test_testrun_unresolvable_raises(mock_polarion):
    bad_data = _zeep_object({'id': 'TR-BAD'}, unresolvable=True)
    with pytest.raises(PolarionNotFoundError):
        Testrun(mock_polarion, polarion_test_run=bad_data)


def test_testrun_uri_not_found_raises(mock_polarion):
    test_mgmt_service = MagicMock()
    test_mgmt_service.getTestRunByUri.side_effect = Exception('Not found')

    def _get_service(name):
        if name == 'TestManagement':
            return test_mgmt_service
        return MagicMock()

    with patch.object(mock_polarion, 'getService', side_effect=_get_service):
        with pytest.raises(PolarionNotFoundError):
            Testrun(mock_polarion, uri='subterra:bad-uri')


# ---------------------------------------------------------------------------
# hasTestCase / getTestCase
# ---------------------------------------------------------------------------

def test_has_test_case_true(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    assert tr.hasTestCase('TC-001') is True


def test_has_test_case_false(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    assert tr.hasTestCase('TC-NONEXISTENT') is False


def test_get_test_case_returns_record(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    record = tr.getTestCase('TC-001')
    assert record is not None
    assert record.testcase_id == 'TC-001'


def test_get_test_case_returns_none_when_missing(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    record = tr.getTestCase('TC-NONEXISTENT')
    assert record is None


# ---------------------------------------------------------------------------
# hasAttachment
# ---------------------------------------------------------------------------

def test_has_attachment_false(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    tr.attachments = None
    assert tr.hasAttachment() is False


def test_has_attachment_true(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    tr.attachments = MagicMock()
    assert tr.hasAttachment() is True


# ---------------------------------------------------------------------------
# isCustomFieldAllowed
# ---------------------------------------------------------------------------

def test_is_custom_field_allowed_always_true(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    assert tr.isCustomFieldAllowed('any_field') is True
    assert tr.isCustomFieldAllowed('another_field') is True


# ---------------------------------------------------------------------------
# __repr__ / __str__
# ---------------------------------------------------------------------------

def test_repr_contains_info(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    r = repr(tr)
    assert 'TR-001' in r
    assert 'Test Run 1' in r


def test_str_equals_repr(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    assert str(tr) == repr(tr)
