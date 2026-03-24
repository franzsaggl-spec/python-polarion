"""Tests for Testrun with mocked SOAP layer (v2.0.0 API)."""

import copy
from unittest.mock import MagicMock, patch

import pytest

from polarion.exceptions import PolarionFieldError, PolarionNotFoundError
from polarion.testrun import Testrun

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_testrun_data():
    """A sample testrun dict as returned by the TestManagement service in v2.0.0."""
    test_record = {
        "testCaseURI": "subterra:data-service:objects:/default/test_project${WorkItem}TC-001",
        "defectURI": None,
        "result": None,
        "comment": None,
        "executed": None,
        "executedByURI": None,
        "duration": None,
        "testStepResults": None,
        "attachments": None,
    }

    return {
        "id": "TR-001",
        "title": "Test Run 1",
        "uri": "subterra:data-service:objects:/default/test_project${TestRun}TR-001",
        "created": "2024-01-01",
        "updated": "2024-01-02",
        "records": [test_record],
        "attachments": None,
        "customFields": None,
        "projectURI": None,
        "type": None,
        "status": None,
        "finishedOn": None,
        "isTemplate": False,
        "document": None,
        "comments": None,
        "author": None,
        "idPrefix": None,
        "groupId": None,
        "homePageContent": None,
        "keepInHistory": None,
        "selectTestCasesBy": None,
        "templateURI": None,
        "query": None,
        "useReportFromTemplate": None,
    }


def _make_testrun(mock_polarion, mock_testrun_data):
    """Build a Testrun from mocked data without hitting SOAP."""
    data = copy.deepcopy(mock_testrun_data)
    tr = Testrun(mock_polarion, polarion_test_run=data)
    return tr


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------


def test_testrun_creation_from_data(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    assert tr.id == "TR-001"
    assert tr.title == "Test Run 1"


def test_testrun_creation_from_uri(mock_polarion, mock_testrun_data):
    data = copy.deepcopy(mock_testrun_data)

    mock_polarion._soap.call.side_effect = None
    mock_polarion._soap.call.return_value = data

    tr = Testrun(mock_polarion, uri=data["uri"])

    assert tr.id == "TR-001"
    mock_polarion._soap.call.assert_called_once_with(
        "TestManagement", "getTestRunByUri", uri=data["uri"]
    )


def test_testrun_neither_uri_nor_data_raises_field_error(mock_polarion):
    with pytest.raises(PolarionFieldError):
        Testrun(mock_polarion)


def test_testrun_unresolvable_raises(mock_polarion):
    bad_data = {"id": "TR-BAD", "unresolvable": True}
    with pytest.raises(PolarionNotFoundError):
        Testrun(mock_polarion, polarion_test_run=bad_data)


def test_testrun_uri_not_found_raises(mock_polarion):
    mock_polarion._soap.call.side_effect = Exception("Not found")

    with pytest.raises(PolarionNotFoundError):
        Testrun(mock_polarion, uri="subterra:bad-uri")


# ---------------------------------------------------------------------------
# has_test_case / get_test_case
# ---------------------------------------------------------------------------


def test_has_test_case_true(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    assert tr.has_test_case("TC-001") is True


def test_has_test_case_false(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    assert tr.has_test_case("TC-NONEXISTENT") is False


def test_get_test_case_returns_record(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    record = tr.get_test_case("TC-001")
    assert record is not None
    assert record.testcase_id == "TC-001"


def test_get_test_case_returns_none_when_missing(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    record = tr.get_test_case("TC-NONEXISTENT")
    assert record is None


# ---------------------------------------------------------------------------
# has_attachment
# ---------------------------------------------------------------------------


def test_has_attachment_false(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    tr.attachments = None
    assert tr.has_attachment() is False


def test_has_attachment_true(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    tr.attachments = [{"id": "att1"}]
    assert tr.has_attachment() is True


# ---------------------------------------------------------------------------
# is_custom_field_allowed
# ---------------------------------------------------------------------------


def test_is_custom_field_allowed_always_true(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    assert tr.is_custom_field_allowed("any_field") is True
    assert tr.is_custom_field_allowed("another_field") is True


# ---------------------------------------------------------------------------
# __repr__ / __str__
# ---------------------------------------------------------------------------


def test_repr_contains_info(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    r = repr(tr)
    assert "TR-001" in r
    assert "Test Run 1" in r


def test_str_equals_repr(mock_polarion, mock_testrun_data):
    tr = _make_testrun(mock_polarion, mock_testrun_data)
    assert str(tr) == repr(tr)
