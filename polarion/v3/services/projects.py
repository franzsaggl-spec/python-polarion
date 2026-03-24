from __future__ import annotations

from ..types.common import Page, UserRef
from ..types.project import Project
from .base import ServiceBase


class ProjectsService(ServiceBase):
    def get(self, project_id: str) -> Project:
        raise NotImplementedError

    def list(self, query: str | None = None, *, offset: int = 0, limit: int = 100) -> Page[Project]:
        raise NotImplementedError

    def users(self, project_id: str, *, offset: int = 0, limit: int = 200) -> Page[UserRef]:
        raise NotImplementedError
