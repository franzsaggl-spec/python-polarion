"""Plan-related project behavior mixin."""

from __future__ import annotations

from typing import Any

from ..plan import Plan


class ProjectPlansMixin:
    def get_plan(self, id: str) -> Plan:
        """Get a plan by ID."""
        return Plan(self.polarion, self, id=id)

    def create_plan(
        self,
        name: str,
        plan_id: str,
        template: str,
        parent: Plan | None = None,
    ) -> Plan:
        """Create a new plan.

        :param name: Plan name
        :param plan_id: Plan ID
        :param template: Template name ("release", "iteration", etc.)
        :param parent: Optional parent plan
        """
        return Plan(
            self.polarion,
            self,
            new_plan_name=name,
            new_plan_id=plan_id,
            new_plan_template=template,
            new_plan_parent=parent,
        )

    def search_plans(self, query: str = "", order: str = "Created", limit: int = 100) -> list[Any]:
        """Search for plans (lightweight results).

        :param query: Polarion query
        :param order: Sort field
        :param limit: Maximum results
        """
        return (
            self.polarion._soap.call(
                "Planning", "searchPlans", query=self._scoped_query(query), sort=order, limit=limit
            )
            or []
        )

    def search_plans_full(self, query: str = "", order: str = "Created", limit: int = 100) -> list[Plan]:
        """Search for plans and return full Plan objects."""
        return [Plan(self.polarion, self, polarion_record=p) for p in self.search_plans(query, order, limit)]
