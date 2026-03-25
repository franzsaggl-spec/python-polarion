from __future__ import annotations

from ..parser.project import parse_project, parse_project_list, parse_user_ref_list
from ..types.common import Page, UserRef
from ..types.project import Project
from .base import ServiceBase


class ProjectsService(ServiceBase):
    def get(self, project_id: str) -> Project:
        raw = self.transport.call("Project", "getProject", projectId=project_id)
        project = parse_project(raw)
        self.require_identifier(project.id, context=f"project {project_id}")
        return project

    def list(self, query: str | None = None, *, offset: int = 0, limit: int = 100) -> Page[Project]:
        # Polarion SOAP API has no generic project search endpoint in the legacy API;
        # `getProjects` returns full list.
        raw = self.transport.call("Project", "getProjects")
        items = parse_project_list(raw)
        if query:
            q = query.lower()
            items = [p for p in items if q in p.id.lower() or q in p.name.lower()]
        sliced = items[offset : offset + limit]
        return Page(
            items=sliced,
            total=len(items),
            offset=offset,
            limit=limit,
            has_more=offset + len(sliced) < len(items),
        )

    def users(self, project_id: str, *, offset: int = 0, limit: int = 200) -> Page[UserRef]:
        raw = self.transport.call("Project", "getProjectUsers", projectId=project_id)
        items = parse_user_ref_list(raw)
        sliced = items[offset : offset + limit]
        return Page(
            items=sliced,
            total=len(items),
            offset=offset,
            limit=limit,
            has_more=offset + len(sliced) < len(items),
        )
