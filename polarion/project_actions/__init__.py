"""Composed behavior mixin for Project."""

from .documents import ProjectDocumentsMixin
from .plans import ProjectPlansMixin
from .testruns import ProjectTestRunsMixin
from .users import ProjectUsersMixin
from .workitems import ProjectWorkitemsMixin


class ProjectActionsMixin(
    ProjectUsersMixin,
    ProjectWorkitemsMixin,
    ProjectTestRunsMixin,
    ProjectPlansMixin,
    ProjectDocumentsMixin,
):
    """Composite mixin preserving Project behavior surface."""
