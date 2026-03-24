"""Tests for Project-level methods with mocked SOAP layer (v2.0.0 API)."""

from polarion.project import Project


def _make_project(mock_polarion, project_id="TEST"):
    """Build a Project from mocked data without hitting SOAP."""
    project_data = {
        "name": "Test Project",
        "trackerPrefix": "TEST",
        "id": project_id,
    }

    mock_polarion._soap.call.return_value = project_data
    proj = Project(mock_polarion, project_id)
    mock_polarion._soap.call.reset_mock()
    return proj


# ------------------------------------------------------------------
# __repr__
# ------------------------------------------------------------------


def test_project_repr(mock_polarion):
    """Project should have a readable repr."""
    proj = _make_project(mock_polarion, "MYPROJ")
    assert "Test Project" in repr(proj)
    assert "TEST" in repr(proj)
