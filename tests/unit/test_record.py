"""Tests for the Record class (v2.0.0 API)."""

from unittest.mock import MagicMock, patch

from polarion.record import Record


def _make_record(mock_polarion, result_id=None, comment_content=None):
    """Build a Record from mocked data."""
    record_data = {
        "result": {"id": result_id} if result_id is not None else None,
        "comment": {"content": comment_content, "type": "text/html", "contentLossy": False}
        if comment_content is not None
        else None,
        "executed": "2024-01-15",
        "executedByURI": None,
        "duration": 120.0,
        "attachments": None,
        "testStepResults": None,
        "testCaseURI": "subterra:data-service:objects:/default/test_project${WorkItem}TC-001",
        "defectURI": None,
        "iteration": None,
    }

    test_run = MagicMock()
    test_run.uri = "subterra:data-service:objects:/default/test_project${TestRun}TR-001"
    test_run.id = "TR-001"

    return Record(mock_polarion, test_run, record_data, index=0)


# ------------------------------------------------------------------
# get_result
# ------------------------------------------------------------------


def test_get_result_passed(mock_polarion):
    rec = _make_record(mock_polarion, result_id="passed")
    assert rec.get_result() == Record.ResultType.PASSED


def test_get_result_failed(mock_polarion):
    rec = _make_record(mock_polarion, result_id="failed")
    assert rec.get_result() == Record.ResultType.FAILED


def test_get_result_blocked(mock_polarion):
    rec = _make_record(mock_polarion, result_id="blocked")
    assert rec.get_result() == Record.ResultType.BLOCKED


def test_get_result_none_returns_no(mock_polarion):
    rec = _make_record(mock_polarion, result_id=None)
    assert rec.get_result() == Record.ResultType.No


# ------------------------------------------------------------------
# get_comment
# ------------------------------------------------------------------


def test_get_comment_returns_content(mock_polarion):
    rec = _make_record(mock_polarion, comment_content="All good")
    assert rec.get_comment() == "All good"


def test_get_comment_returns_none(mock_polarion):
    rec = _make_record(mock_polarion, comment_content=None)
    assert rec.get_comment() is None


def test_get_comment_with_html(mock_polarion):
    rec = _make_record(mock_polarion, comment_content="<b>Bold comment</b>")
    assert rec.get_comment() == "<b>Bold comment</b>"


# ------------------------------------------------------------------
# testcase_id property
# ------------------------------------------------------------------


def test_testcase_id_property(mock_polarion):
    rec = _make_record(mock_polarion)
    # The testCaseURI is '...${WorkItem}TC-001', split on '}' gives 'TC-001'
    assert rec.testcase_id == "TC-001"


def test_testcase_id_matches_get_test_case_name(mock_polarion):
    rec = _make_record(mock_polarion)
    assert rec.testcase_id == rec.get_test_case_name()


# ------------------------------------------------------------------
# Context manager (batch save)
# ------------------------------------------------------------------


def test_context_manager_sets_batch_save(mock_polarion):
    rec = _make_record(mock_polarion, result_id="passed")
    with patch.object(rec, "save") as mock_save:
        with rec:
            assert rec._batch_save is True
        assert rec._batch_save is False
    # __exit__ calls save once
    mock_save.assert_called_once()


def test_context_manager_calls_save_on_exit(mock_polarion):
    rec = _make_record(mock_polarion, result_id="passed")
    with patch.object(rec, "save") as mock_save:
        with rec:
            pass
        mock_save.assert_called_once()


def test_save_returns_early_when_batch_save(mock_polarion):
    """When _batch_save is True, save() should return immediately."""
    rec = _make_record(mock_polarion, result_id="passed")
    rec._batch_save = True

    # If save actually tried to talk to the service, _soap.call would be called
    mock_polarion._soap.call.reset_mock()
    rec.save()
    mock_polarion._soap.call.assert_not_called()


# ------------------------------------------------------------------
# __str__ and __repr__
# ------------------------------------------------------------------


def test_str_includes_testcase_name(mock_polarion):
    rec = _make_record(mock_polarion, result_id="passed")
    s = str(rec)
    assert "TC-001" in s
    assert "TR-001" in s


def test_repr_includes_testcase_name(mock_polarion):
    rec = _make_record(mock_polarion, result_id="passed")
    r = repr(rec)
    assert "TC-001" in r
