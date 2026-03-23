from __future__ import annotations

import copy
from datetime import date, datetime
from typing import Any, Optional, TYPE_CHECKING

from .base.polarion_object import PolarionObject
from .exceptions import PolarionNotFoundError, PolarionFieldError
from .factory import Creator
from .workitem import Workitem

if TYPE_CHECKING:
    from .polarion import Polarion
    from .project import Project


class Plan(PolarionObject):
    """
    A polarion Plan
    """

    def __init__(self, polarion: Polarion, project: Optional[Project], polarion_record: Optional[Any] = None, uri: Optional[str] = None, id: Optional[str] = None, new_plan_name: Optional[str] = None, new_plan_id: Optional[str] = None, new_plan_parent: Optional[Plan] = None,
                 new_plan_template: Optional[str] = None) -> None:
        """

        :param polarion: Polarion client
        :param project: Polarion project
        :param polarion_record:
        :param uri: uri for the Plan
        :param id:  id for the Plan
        :param new_plan_name: new plan name, if a new plan needs to be constructed, also supply new_plan_id and new_plan_template
        :param new_plan_id:  new plan id
        :param new_plan_parent: optional new plan parent
        :param new_plan_template: plan template, defaults in polarion are iteration or release
        """
        super().__init__(polarion, project, id, uri)
        self._polarion_record = polarion_record

        if new_plan_id is not None and new_plan_name is not None:
            # get the ID from the plan if the ID if the plan is passed
            if isinstance(new_plan_parent, Plan):
                new_plan_parent = new_plan_parent.id
            service = self._polarion.getService('Planning')
            self._uri = service.createPlan(self._project.id, new_plan_name, new_plan_id, new_plan_parent, new_plan_template)

        if self._uri is not None:
            service = self._polarion.getService('Planning')
            self._polarion_record = service.getPlanByUri(self._uri)

        if self._id is not None:
            service = self._polarion.getService('Planning')
            self._polarion_record = service.getPlanById(self._project.id, self._id)

        self._buildPlanFromPolarion()

    def _buildPlanFromPolarion(self) -> None:
        if self._polarion_record is not None and not self._polarion_record.unresolvable:
            self._populate_attrs(self, self._polarion_record)
            self._original_polarion = copy.deepcopy(self._polarion_record)
        else:
            raise PolarionNotFoundError('Plan not retrieved from Polarion')

    def setDueDate(self, date: date | datetime) -> None:
        """
        Set the due date for this plan
        :param date: date object
        :return: None
        """
        self.dueDate = date
        self.save()

    def setStartDate(self, date: date | datetime) -> None:
        """
        Set the start date for this plan
        :param date: date object
        :return: None
        """
        self.startDate = date
        self.save()

    def setFinishedOnDate(self, date: date | datetime) -> None:
        """
        Set the finished date for this plan
        :param date: date object
        :return: None
        """
        self.finishedOn = date
        self.save()

    def setStartedOnDate(self, date: date | datetime) -> None:
        """
        Set the started on date for this plan
        :param date: date object
        :return: None
        """
        self.startedOn = date
        self.save()

    def addToPlan(self, workitem: Workitem) -> None:
        """
        Add a workitem to the plan
        :param workitem: Workitem
        :return: None
        """
        if any(x.id == workitem.type.id for x in self.allowedTypes.EnumOptionId):
            service = self._polarion.getService('Planning')
            service.addPlanItems(self.uri, [workitem.uri])
            workitem._reloadFromPolarion()  # noqa: SLF001 - reload so the plan status is updated
            self._reloadFromPolarion()
        else:
            raise PolarionFieldError(f'Workitem type {workitem.id} is not allowed in this plan')

    def removeFromPlan(self, workitem: Workitem) -> None:
        """
        Remove a workitem from the plan
        :param workitem: Workitem
        :return: None
        """
        service = self._polarion.getService('Planning')
        service.removePlanItems(self.uri, [workitem.uri])
        workitem._reloadFromPolarion()  # noqa: SLF001 - reload so the plan status is updated
        self._reloadFromPolarion()

    def addAllowedType(self, type: str) -> None:
        """
        Add an allowed workitem type to this plan
        :param type: a string with the type name
        :return: None
        """
        if not any(x.id == type for x in self.allowedTypes.EnumOptionId):
            service = self._polarion.getService('Planning')
            service.addPlanAllowedType(self.uri, self._polarion.EnumOptionIdType(id=type))
            self._reloadFromPolarion()

    def removeAllowedType(self, type: str) -> None:
        """
        Remove an allowed workitem type to this plan
        :param type: a string with the type name
        :return: None
        """
        if any(x.id == type for x in self.allowedTypes.EnumOptionId):
            service = self._polarion.getService('Planning')
            service.removePlanAllowedType(self.uri, self._polarion.EnumOptionIdType(id=type))
            self._reloadFromPolarion()

    def getWorkitemsInPlan(self) -> list[Workitem]:
        """
        Get all workitems from this plan

        ⚠️ Performance warning: Fetches all workitems in the plan as full objects.
        For plans with many workitems, consider using project.searchWorkitem() with a
        query filter to fetch only the workitems you need.

        :return: Array of workitems
        """
        if self.records is None:
            return []
        return [Workitem(self._polarion, self._project, polarion_workitem=r.item)
                for r in self.records.PlanRecord if r.item.id is not None]

    def save(self) -> None:
        """
        Update the plan in polarion
        """
        updated_plan = self._build_update_dict(self, self._polarion_record, self._original_polarion)
        if updated_plan:
            updated_plan['uri'] = self.uri
            service = self._polarion.getService('Planning')
            service.updatePlan(updated_plan)
            self._reloadFromPolarion()

    def getParent(self) -> Plan:
        """
        Get the parent plan
        :return: parent Plan
        """
        return Plan(self._polarion, self._project, self.parent)

    def getChildren(self) -> list[Plan]:
        """
        Get the child plans
        :return: List of Plans, or empty list if there are no children.
        """
        return [p for p in self._project.searchPlanFullItem(f'parent.id:{self.id}') if p.id != self.id]


    def _reloadFromPolarion(self) -> None:
        service = self._polarion.getService('Planning')
        self._polarion_record = service.getPlanByUri(self._polarion_record.uri)
        self._buildPlanFromPolarion()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Plan):
            return NotImplemented
        return self.id == other.id

    def to_dict(self, fields: Optional[list[str]] = None) -> dict[str, Any]:
        """
        Return a dictionary representation of the plan.

        :param fields: List of field names to include. If None, returns minimal summary with: id, name, startDate, dueDate
        :return: Dictionary with requested fields
        :rtype: dict
        """
        if fields is None:
            # Return minimal summary for context efficiency
            fields = ['id', 'name', 'startDate', 'dueDate']

        result = {}
        for field in fields:
            if hasattr(self, field):
                value = getattr(self, field)
                # Convert complex objects to simple representations
                if hasattr(value, '__dict__') and not isinstance(value, (str, int, float, bool, date, datetime)):
                    if hasattr(value, 'id'):
                        result[field] = value.id
                    else:
                        result[field] = str(value)
                else:
                    result[field] = value

        return result

    def __repr__(self) -> str:
        return f'{self.name} ({self.id})'

    __str__ = __repr__


class PlanCreator(Creator):
    def createFromUri(self, polarion: Polarion, project: Optional[Project], uri: str) -> Plan:
        return Plan(polarion, None, uri)
