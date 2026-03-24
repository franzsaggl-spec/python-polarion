"""Polarion Project model."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .exceptions import PolarionApiError, PolarionNotFoundError
from .project_actions import ProjectActionsMixin
from .utils import ensure_dict

if TYPE_CHECKING:
    from .client import Polarion

logger = logging.getLogger(__name__)


class Project(ProjectActionsMixin):
    """A Polarion project.

    :param polarion: Polarion client instance
    :param project_id: The project ID (as in the Polarion URL)
    """

    def __init__(self, polarion: Polarion, project_id: str) -> None:
        self.polarion = polarion
        self.id = project_id

        try:
            self.polarion_data = self.polarion._soap.call("Project", "getProject", projectId=self.id)
        except PolarionApiError as e:
            raise PolarionNotFoundError(f"Could not find project {project_id}") from e

        project_data = ensure_dict(self.polarion_data)
        if project_data and not project_data.get("unresolvable"):
            self.name = str(project_data.get("name", ""))
            self.tracker_prefix = str(project_data.get("trackerPrefix", ""))
        else:
            raise PolarionNotFoundError(f"Could not find project {project_id}")

    def __repr__(self) -> str:
        return f"Polarion project {self.name} prefix {self.tracker_prefix}"

    __str__ = __repr__
