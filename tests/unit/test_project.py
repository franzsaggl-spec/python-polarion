"""Tests for Project-level methods with mocked SOAP layer."""

import pytest
from unittest.mock import MagicMock, patch

from polarion.project import Project


def _make_project(mock_polarion, project_id='TEST'):
    """Build a Project from mocked data without hitting SOAP."""
    project_service = MagicMock()

    # Mock project data
    project_data = MagicMock()
    project_data.name = 'Test Project'
    project_data.trackerPrefix = 'TEST'
    project_data.unresolvable = False
    project_data.__contains__ = lambda self, key: key in ['name', 'trackerPrefix']

    project_service.getProject.return_value = project_data

    def _get_service(name):
        if name == 'Project':
            return project_service
        return MagicMock()

    with patch.object(mock_polarion, 'getService', side_effect=_get_service):
        proj = Project(mock_polarion, project_id)

    mock_polarion.getService = MagicMock(side_effect=_get_service)
    return proj


# ------------------------------------------------------------------
# __repr__
# ------------------------------------------------------------------

def test_project_repr(mock_polarion):
    """Project should have a readable repr."""
    proj = _make_project(mock_polarion, 'MYPROJ')
    assert 'Test Project' in repr(proj)
    assert 'TEST' in repr(proj)
