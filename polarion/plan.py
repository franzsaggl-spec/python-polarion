"""Polarion Plan model."""

from __future__ import annotations

import copy
import logging
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from .base.polarion_object import PolarionObject
from .exceptions import PolarionApiError, PolarionFieldError, PolarionNotFoundError
from .factory import Creator
from .utils import ensure_list
from .workitem import Workitem

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .client import Polarion
    from .project import Project


class Plan(PolarionObject):
    """A Polarion plan.

    :param polarion: Polarion client
    :param project: Project instance
    :param id: Plan ID
    :param uri: Plan URI
    :param polarion_record: Pre-fetched plan data
    :param new_plan_name: Name for creating a new plan
    :param new_plan_id: ID for the new plan
    :param new_plan_template: Template ("iteration", "release")
    :param new_plan_parent: Parent plan
    """

    _default_summary_fields = ["id", "name", "startDate", "dueDate"]

    # Declared attributes
    id: str | None = None
    name: str | None = None
    startDate: date | datetime | None = None
    dueDate: date | datetime | None = None
    finishedOn: date | datetime | None = None
    startedOn: date | datetime | None = None
    allowedTypes: Any = None
    records: Any = None
    parent: Any = None

    def __init__(
        self,
        polarion: Polarion,
        project: Project | None,
        polarion_record: dict[str, Any] | None = None,
        uri: str | None = None,
        id: str | None = None,
        new_plan_name: str | None = None,
        new_plan_id: str | None = None,
        new_plan_parent: Plan | None = None,
        new_plan_template: str | None = None,
    ) -> None:
        super().__init__(polarion, project, id, uri)
        self._polarion_record = polarion_record or {}
        self._original_data: dict[str, Any] = {}

        if new_plan_id is not None and new_plan_name is not None:
            parent_id = new_plan_parent.id if isinstance(new_plan_parent, Plan) else new_plan_parent
            self._uri = self._polarion._soap.call(
                "Planning",
                "createPlan",
                projectId=self._project.id,
                planName=new_plan_name,
                planId=new_plan_id,
                parentPlanId=parent_id,
                templateId=new_plan_template,
            )

        if self._uri is not None:
            self._polarion_record = self._polarion._soap.call("Planning", "getPlanByUri", uri=self._uri)

        if self._id is not None and not self._polarion_record:
            self._polarion_record = self._polarion._soap.call(
                "Planning", "getPlanById", projectId=self._project.id, planId=self._id
            )

        self._build_from_polarion()

    def _build_from_polarion(self) -> None:
        if isinstance(self._polarion_record, dict) and not self._polarion_record.get("unresolvable"):
            self._populate_from_dict(self, self._polarion_record)
            self._original_data = copy.deepcopy(self._polarion_record)
            self._uri = self._polarion_record.get("uri", self._uri)
        else:
            raise PolarionNotFoundError("Plan not retrieved from Polarion")

    def set_due_date(self, due_date: date | datetime) -> None:
        """Set the due date."""
        self.dueDate = due_date

    def set_start_date(self, start_date: date | datetime) -> None:
        """Set the start date."""
        self.startDate = start_date

    def set_finished_on_date(self, finished_on: date | datetime) -> None:
        """Set the finished date."""
        self.finishedOn = finished_on

    def set_started_on_date(self, started_on: date | datetime) -> None:
        """Set the started on date."""
        self.startedOn = started_on

    def add_workitem(self, workitem: Workitem) -> None:
        """Add a work item to this plan.

        :param workitem: Work item to add
        :raises PolarionFieldError: If the work item type is not allowed
        """
        allowed = self.allowedTypes
        if isinstance(allowed, dict):
            enum_list = allowed.get("EnumOptionId", [])
            if isinstance(enum_list, list):
                wi_type = workitem.type.get("id") if isinstance(workitem.type, dict) else str(workitem.type)
                if not any((e.get("id") if isinstance(e, dict) else str(e)) == wi_type for e in enum_list):
                    raise PolarionFieldError(f"Workitem type {wi_type} not allowed in this plan")

        self._polarion._soap.call("Planning", "addPlanItems", planURI=self.uri, itemURIs=[workitem.uri])
        workitem._reload_from_polarion()
        self._reload_from_polarion()

    def remove_workitem(self, workitem: Workitem) -> None:
        """Remove a work item from this plan."""
        self._polarion._soap.call("Planning", "removePlanItems", planURI=self.uri, itemURIs=[workitem.uri])
        workitem._reload_from_polarion()
        self._reload_from_polarion()

    def add_allowed_type(self, type_name: str) -> None:
        """Add an allowed work item type."""
        self._polarion._soap.call("Planning", "addPlanAllowedType", planURI=self.uri, typeId={"id": type_name})
        self._reload_from_polarion()

    def remove_allowed_type(self, type_name: str) -> None:
        """Remove an allowed work item type."""
        self._polarion._soap.call("Planning", "removePlanAllowedType", planURI=self.uri, typeId={"id": type_name})
        self._reload_from_polarion()

    def get_workitems(self) -> list[Workitem]:
        """Get all work items in this plan."""
        record_list = ensure_list(self.records)
        workitems = []
        for r in record_list:
            if isinstance(r, dict):
                item = r.get("item", {})
                if isinstance(item, dict) and item.get("id") is not None:
                    try:
                        workitems.append(Workitem(self._polarion, self._project, polarion_workitem=item))
                    except (PolarionApiError, PolarionNotFoundError, PolarionFieldError) as e:
                        logger.warning("Skipping unresolvable plan workitem %s: %s", item.get("id", "unknown"), e)
        return workitems

    def get_parent(self) -> Plan:
        """Get the parent plan."""
        return Plan(self._polarion, self._project, self.parent)

    def get_children(self) -> list[Plan]:
        """Get child plans."""
        results = self._project.search_plans_full(f"parent.id:{self.id}")
        return [p for p in results if p.id != self.id]

    def save(self) -> None:
        """Save plan changes to Polarion."""
        changed = self._collect_changes(self, self._polarion_record, self._original_data)
        if changed:
            changed["uri"] = self.uri
            self._polarion._soap.call("Planning", "updatePlan", content=changed)
            self._reload_from_polarion()

    def _reload_from_polarion(self) -> None:
        self._polarion_record = self._polarion._soap.call(
            "Planning", "getPlanByUri", uri=self._polarion_record.get("uri", self._uri)
        )
        self._build_from_polarion()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Plan):
            return NotImplemented
        return self.id == other.id

    def __repr__(self) -> str:
        return f"{self._truncate(self.name)} ({self.id})"

    __str__ = __repr__


class PlanCreator(Creator):
    def create_from_uri(self, polarion: Polarion, project: Project | None, uri: str) -> Plan:
        return Plan(polarion, None, uri=uri)
