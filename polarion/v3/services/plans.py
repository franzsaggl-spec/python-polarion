from __future__ import annotations

from ..parser.plan import parse_plan, parse_plan_list
from ..parser.workitem import parse_workitem_summary_list
from ..types.common import Page
from ..types.plan import Plan, PlanCreate
from ..types.workitem import WorkitemSummary
from .base import ServiceBase


class PlansService(ServiceBase):
    def get(self, project_id: str, plan_id: str) -> Plan:
        raw = self.transport.call("Planning", "getPlanById", projectId=project_id, id=plan_id)
        plan = parse_plan(raw)
        self.require_identifier(plan.id, context=f"plan {plan_id}")
        return plan

    def create(self, project_id: str, payload: PlanCreate) -> Plan:
        raw = self.transport.call(
            "Planning",
            "createPlan",
            projectId=project_id,
            name=payload.name,
            id=payload.plan_id,
            template=payload.template,
            parentId=payload.parent_id,
        )
        return parse_plan(raw)

    def update(self, plan: Plan) -> Plan:
        raw = self.transport.call("Planning", "updatePlan", uri=plan.uri, name=plan.name)
        return parse_plan(raw)

    def delete(self, project_id: str, plan_id: str) -> None:
        self.transport.call("Planning", "deletePlan", projectId=project_id, id=plan_id)

    def search(
        self,
        project_id: str,
        query: str | None = None,
        *,
        sort: str = "Created",
        offset: int = 0,
        limit: int = 100,
    ) -> Page[Plan]:
        raw = self.transport.call("Planning", "searchPlans", projectId=project_id, query=query or "", sort=sort)
        items = parse_plan_list(raw)
        sliced = items[offset : offset + limit]
        return Page(
            items=sliced, total=len(items), offset=offset, limit=limit, has_more=offset + len(sliced) < len(items)
        )

    def workitems(self, project_id: str, plan_id: str, *, offset: int = 0, limit: int = 200) -> Page[WorkitemSummary]:
        # Query by plan id relation; backend specifics may vary but this keeps v3 contract functional.
        raw = self.transport.call(
            "Tracker",
            "queryWorkItems",
            query=f"project.id:{project_id} AND plan.id:{plan_id}",
            sort="id",
            fields=["id", "title", "type", "status", "priority"],
        )
        items = parse_workitem_summary_list(raw)
        sliced = items[offset : offset + limit]
        return Page(
            items=sliced, total=len(items), offset=offset, limit=limit, has_more=offset + len(sliced) < len(items)
        )

    def add_workitem(self, project_id: str, plan_id: str, workitem_id: str) -> None:
        self.transport.call("Planning", "addPlanItems", projectId=project_id, planId=plan_id, itemIds=[workitem_id])

    def remove_workitem(self, project_id: str, plan_id: str, workitem_id: str) -> None:
        self.transport.call("Planning", "removePlanItems", projectId=project_id, planId=plan_id, itemIds=[workitem_id])
