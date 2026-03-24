"""Tests for key workitem functionality with mocked SOAP layer."""

from unittest.mock import MagicMock, patch

from polarion.workitem import Workitem


def _make_workitem(mock_polarion, mock_project, mock_workitem_data):
    """Build a Workitem from mocked data without hitting SOAP.

    We mock getService so that:
    - Tracker.getWorkItemById returns mock_workitem_data
    - Tracker.getCustomFieldKeys returns [] (no test step field)
    - TestManagement.getTestSteps returns a stub
    """
    tracker_service = MagicMock()
    tracker_service.getWorkItemById.return_value = mock_workitem_data
    tracker_service.getCustomFieldKeys.return_value = []

    test_mgmt_service = MagicMock()
    test_mgmt_service.getTestSteps.return_value = MagicMock(keys=None, steps=None)

    def _get_service(name):
        if name == "Tracker":
            return tracker_service
        if name == "TestManagement":
            return test_mgmt_service
        return MagicMock()

    with patch.object(mock_polarion, "getService", side_effect=_get_service):
        wi = Workitem(mock_polarion, mock_project, id="WI-001")

    # Re-patch getService for any subsequent calls the test might trigger
    mock_polarion.getService = MagicMock(side_effect=_get_service)
    wi._tracker_service = tracker_service
    return wi


# ------------------------------------------------------------------
# getDescription
# ------------------------------------------------------------------


def test_get_description_returns_content(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    assert wi.getDescription() == "<p>Test description</p>"


def test_get_description_returns_none_when_empty(mock_polarion, mock_project, mock_workitem_data):
    mock_workitem_data.description = None
    mock_workitem_data.__dict__["__values__"]["description"] = None
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    assert wi.getDescription() is None


# ------------------------------------------------------------------
# setDescription
# ------------------------------------------------------------------


def test_set_description_calls_save(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    with patch.object(wi, "save") as mock_save:
        wi.setDescription("new desc")
        mock_save.assert_called_once()


# ------------------------------------------------------------------
# hasTestSteps
# ------------------------------------------------------------------


def test_has_test_steps_false_when_none(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    # _parsed_test_steps is None by default when no steps are configured
    wi._parsed_test_steps = None
    assert wi.hasTestSteps() is False


def test_has_test_steps_false_when_empty(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    wi._parsed_test_steps = []
    assert wi.hasTestSteps() is False


def test_has_test_steps_true_when_present(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    wi._parsed_test_steps = [{"step": "do something", "expected": "it works"}]
    assert wi.hasTestSteps() is True


# ------------------------------------------------------------------
# getStatusEnum, getResolutionEnum, getSeverityEnum
# ------------------------------------------------------------------


def test_get_status_enum_returns_empty_on_error(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    wi._project = MagicMock()
    wi._project.getEnum.side_effect = Exception("enum error")
    assert wi.getStatusEnum() == []


def test_get_resolution_enum_returns_empty_on_error(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    wi._project = MagicMock()
    wi._project.getEnum.side_effect = Exception("enum error")
    assert wi.getResolutionEnum() == []


def test_get_severity_enum_returns_empty_on_error(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    wi._project = MagicMock()
    wi._project.getEnum.side_effect = Exception("enum error")
    assert wi.getSeverityEnum() == []


def test_get_status_enum_returns_values(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    wi._project = MagicMock()
    wi._project.getEnum.return_value = ["open", "closed", "in_progress"]
    assert wi.getStatusEnum() == ["open", "closed", "in_progress"]


# ------------------------------------------------------------------
# hasAttachment
# ------------------------------------------------------------------


def test_has_attachment_false(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    wi.attachments = None
    assert wi.hasAttachment() is False


def test_has_attachment_true(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    wi.attachments = MagicMock()  # non-None
    assert wi.hasAttachment() is True


# ------------------------------------------------------------------
# Context manager (__enter__ / __exit__)
# ------------------------------------------------------------------


def test_context_manager_postpones_save(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)

    with patch.object(wi, "save") as mock_save:
        with wi:
            assert wi._postpone_save is True
            # Calling save inside the context should be a no-op because
            # postpone is True and the real save checks for it
            wi.save()
        # __exit__ should set postpone to False and call save
        assert wi._postpone_save is False
    # save was called: once from our explicit call inside `with` (no-op due to postpone)
    # and once from __exit__
    assert mock_save.call_count == 2


def test_context_manager_sets_postpone_false_on_exit(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    with patch.object(wi, "save"):
        with wi:
            pass
    assert wi._postpone_save is False


# ------------------------------------------------------------------
# __eq__
# ------------------------------------------------------------------


def test_eq_same_workitem(mock_polarion, mock_project, mock_workitem_data):
    wi1 = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    wi2 = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    assert wi1 == wi2


def test_eq_different_type(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    assert wi != "not a workitem"
    assert wi != 42
    assert wi != None  # noqa: E711 -- intentional None comparison


# ------------------------------------------------------------------
# __str__ and __repr__
# ------------------------------------------------------------------


def test_str_contains_id_and_title(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    s = str(wi)
    assert "WI-001" in s
    assert "Test workitem" in s


def test_repr_contains_id_and_title(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    r = repr(wi)
    assert "WI-001" in r
    assert "Test workitem" in r


# ------------------------------------------------------------------
# save() when nothing changed
# ------------------------------------------------------------------


def test_save_no_changes_does_not_call_update(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    tracker_service = MagicMock()
    mock_polarion.getService = MagicMock(return_value=tracker_service)

    wi.save()
    tracker_service.updateWorkItem.assert_not_called()


# ------------------------------------------------------------------
# getLinkedItem returns empty when no links
# ------------------------------------------------------------------


def test_get_linked_item_empty_when_no_links(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    wi.linkedWorkItems = None
    wi.linkedWorkItemsDerived = None
    assert wi.getLinkedItem() == []


# ------------------------------------------------------------------
# getAssignedUsers returns empty when assignee is None
# ------------------------------------------------------------------


def test_get_assigned_users_empty_when_none(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    wi.assignee = None
    assert wi.getAssignedUsers() == []


# ------------------------------------------------------------------
# getApproverUsers returns empty when approvals is None
# ------------------------------------------------------------------


def test_get_approver_users_empty_when_none(mock_polarion, mock_project, mock_workitem_data):
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    wi.approvals = None
    assert wi.getApproverUsers() == []


# ------------------------------------------------------------------
# to_dict()
# ------------------------------------------------------------------


def test_to_dict_default_fields(mock_polarion, mock_project, mock_workitem_data):
    """to_dict() with no args should return minimal summary fields."""
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    result = wi.to_dict()

    # Default fields: id, title, type, status
    assert "id" in result
    assert "title" in result
    assert "type" in result
    assert "status" in result

    assert result["id"] == "WI-001"
    assert result["title"] == "Test workitem"
    assert len(result) == 4  # Only the 4 minimal fields


def test_to_dict_custom_fields(mock_polarion, mock_project, mock_workitem_data):
    """to_dict() should return only requested fields."""
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    result = wi.to_dict(fields=["id", "title"])

    assert "id" in result
    assert "title" in result
    assert "type" not in result
    assert "status" not in result
    assert len(result) == 2


def test_to_dict_handles_missing_field(mock_polarion, mock_project, mock_workitem_data):
    """to_dict() should skip missing fields gracefully."""
    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    result = wi.to_dict(fields=["id", "nonexistent_field"])

    assert "id" in result
    # nonexistent_field should be skipped, not crash
    assert "nonexistent_field" not in result


# ------------------------------------------------------------------
# __repr__ truncation
# ------------------------------------------------------------------


def test_repr_truncates_long_title(mock_polarion, mock_project, mock_workitem_data):
    """__repr__ should truncate titles longer than 50 chars."""
    # Set a long title
    long_title = "A" * 100
    mock_workitem_data.title = long_title
    mock_workitem_data.__dict__["__values__"]["title"] = long_title

    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    r = repr(wi)

    # Should contain truncated title with ellipsis
    assert "WI-001" in r
    assert "..." in r
    assert len(r) < len(long_title)  # Much shorter than full title


def test_repr_does_not_truncate_short_title(mock_polarion, mock_project, mock_workitem_data):
    """__repr__ should not truncate titles 50 chars or less."""
    short_title = "Short title"
    mock_workitem_data.title = short_title
    mock_workitem_data.__dict__["__values__"]["title"] = short_title

    wi = _make_workitem(mock_polarion, mock_project, mock_workitem_data)
    r = repr(wi)

    assert short_title in r
    assert "..." not in r
