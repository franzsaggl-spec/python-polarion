from __future__ import annotations

from ..types.common import Page
from ..types.plan import Plan, PlanCreate
from ..types.workitem import WorkitemSummary
from .base import ServiceBase


class PlansService(ServiceBase):
    def get(self, project_id: str, plan_id: str) -> Plan:
        raise NotImplementedError

    def create(self, project_id: str, payload: PlanCreate) -> Plan:
        raise NotImplementedError

    def update(self, plan: Plan) -> Plan:
        raise NotImplementedError

    def delete(self, project_id: str, plan_id: str) -> None:
        raise NotImplementedError

    def search(
        self,
        project_id: str,
        query: str | None = None,
        *,
        sort: str = "Created",
        offset: int = 0,
        limit: int = 100,
    ) -> Page[Plan]:
        raise NotImplementedError

    def workitems(self, project_id: str, plan_id: str, *, offset: int = 0, limit: int = 200) -> Page[WorkitemSummary]:
        raise NotImplementedError

    def add_workitem(self, project_id: str, plan_id: str, workitem_id: str) -> None:
        raise NotImplementedError

    def remove_workitem(self, project_id: str, plan_id: str, workitem_id: str) -> None:
        raise NotImplementedError
