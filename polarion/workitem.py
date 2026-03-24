"""Polarion Work Item model."""

from __future__ import annotations

import copy
import logging
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from .base.comments import Comments
from .base.custom_fields import CustomFields
from .base.polarion_object import BatchSaveMixin
from .exceptions import PolarionApiError, PolarionFieldError, PolarionNotFoundError
from .factory import Creator
from .utils import ensure_list
from .workitem_actions import WorkitemActionsMixin

if TYPE_CHECKING:
    from .client import Polarion
    from .project import Project

logger = logging.getLogger(__name__)


class Workitem(WorkitemActionsMixin, CustomFields, Comments, BatchSaveMixin):
    """A Polarion work item.

    :param polarion: Polarion client
    :param project: Project instance
    :param id: Work item ID (e.g. "REQ-123")
    :param uri: Work item URI
    :param new_workitem_type: Type for creating a new work item
    :param new_workitem_fields: Fields for the new work item
    :param polarion_workitem: Pre-fetched work item data dict

    Exactly one of ``id``, ``uri``, ``new_workitem_type``, or ``polarion_workitem``
    must be provided.
    """

    _default_summary_fields = ["id", "title", "type", "status"]
    _field_accessors = {"id": lambda self: self._id}

    class HyperlinkRoles(Enum):
        INTERNAL_REF = "internal reference"
        EXTERNAL_REF = "external reference"

    title: str | None = None
    type: Any = None
    status: Any = None
    description: Any = None
    author: Any = None
    assignee: Any = None
    approvals: Any = None
    attachments: Any = None
    categories: Any = None
    comments: Any = None
    created: datetime | None = None
    dueDate: date | None = None
    hyperlinks: Any = None
    initialEstimate: str | None = None
    linkedWorkItems: Any = None
    linkedWorkItemsDerived: Any = None
    location: str | None = None
    outlineNumber: str | None = None
    plannedEnd: datetime | None = None
    plannedStart: datetime | None = None
    priority: Any = None
    resolution: Any = None
    severity: Any = None
    timePoint: Any = None
    updated: datetime | None = None

    def __init__(
        self,
        polarion: Polarion,
        project: Project,
        id: str | None = None,
        uri: str | None = None,
        new_workitem_type: str | None = None,
        new_workitem_fields: dict[str, Any] | None = None,
        polarion_workitem: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(polarion, project, id, uri)
        self._polarion_data: dict[str, Any] = {}
        self._original_data: dict[str, Any] = {}

        if self._uri:
            try:
                self._polarion_data = self._polarion._soap.call("Tracker", "getWorkItemByUri", uri=self._uri)
                if isinstance(self._polarion_data, dict):
                    self._id = self._polarion_data.get("id")
            except PolarionApiError as e:
                raise PolarionNotFoundError(f"Cannot find workitem at URI {self._uri}") from e

        elif id is not None:
            try:
                self._polarion_data = self._polarion._soap.call(
                    "Tracker",
                    "getWorkItemById",
                    projectId=self._project.id,
                    workitemId=self._id,
                )
            except PolarionApiError as e:
                raise PolarionNotFoundError(f"Cannot find workitem {self._id} in project {self._project.id}") from e

        elif new_workitem_type is not None:
            self._create_new(new_workitem_type, new_workitem_fields)

        elif polarion_workitem is not None:
            self._polarion_data = polarion_workitem
            if isinstance(self._polarion_data, dict):
                self._id = self._polarion_data.get("id")

        else:
            raise PolarionFieldError("No id, uri, workitem data, or new workitem type specified")

        self._build_from_polarion()

    def _create_new(self, workitem_type: str, fields: dict[str, Any] | None) -> None:
        """Create a new work item on the server."""
        new_item: dict[str, Any] = {
            "type": {"id": workitem_type},
            "project": {"id": self._project.id},
        }

        # Check required fields
        try:
            required = self._polarion._soap.call(
                "Tracker",
                "getInitialWorkflowActionForProjectAndType",
                projectId=self._project.id,
                typeId={"id": workitem_type},
            )
            if isinstance(required, dict):
                req_features = required.get("requiredFeatures", {})
                if req_features:
                    items = req_features.get("item", [])
                    if isinstance(items, str):
                        items = [items]
                    if fields is None or not set(items) <= fields.keys():
                        raise PolarionFieldError(f"New workitem requires fields: {items} via new_workitem_fields")
        except PolarionFieldError:
            raise
        except PolarionApiError as e:
            logger.debug("Could not check required fields (may not be supported): %s", e)
        except (TypeError, ValueError, KeyError) as e:
            logger.warning("Unexpected error checking required fields: %s", e)

        if fields is not None:
            new_item.update(fields)

        new_uri = self._polarion._soap.call("Tracker", "createWorkItem", content=new_item)
        self._polarion_data = self._polarion._soap.call("Tracker", "getWorkItemByUri", uri=new_uri)
        if isinstance(self._polarion_data, dict):
            self._id = self._polarion_data.get("id")

    def _build_from_polarion(self) -> None:
        """Populate attributes from parsed SOAP data."""
        if not isinstance(self._polarion_data, dict):
            raise PolarionNotFoundError("Workitem not retrieved from Polarion")
        if self._polarion_data.get("unresolvable"):
            raise PolarionNotFoundError("Workitem is unresolvable")

        self._original_data = copy.deepcopy(self._polarion_data)
        self._populate_from_dict(self, self._polarion_data)
        self._uri = self._polarion_data.get("uri", self._uri)

        # Load test steps
        self._polarion_test_steps: dict[str, Any] | None = None
        self._parsed_test_steps: list[dict[str, str]] | None = None
        try:
            if self._has_test_step_field():
                self._polarion_test_steps = self._polarion._soap.call(
                    "TestManagement", "getTestSteps", workitemURI=self.uri
                )
        except PolarionApiError as e:
            logger.warning("Could not fetch test steps for workitem %s: %s", self._id, e)

        if self._polarion_test_steps is not None and isinstance(self._polarion_test_steps, dict):
            keys = self._polarion_test_steps.get("keys")
            steps = self._polarion_test_steps.get("steps")
            if keys is not None and steps is not None:
                columns = self._extract_enum_ids(keys)
                step_list = ensure_list(steps)
                self._parsed_test_steps = []
                for row in step_list:
                    if isinstance(row, dict):
                        values = row.get("values", {})
                        texts = values if isinstance(values, list) else [values]
                        text_contents = [t.get("content", "") if isinstance(t, dict) else str(t) for t in texts]
                        self._parsed_test_steps.append(dict(zip(columns, text_contents)))

    @staticmethod
    def _extract_enum_ids(keys_data: Any) -> list[str]:
        """Extract enum option IDs from keys data."""
        if isinstance(keys_data, dict):
            enum_list = keys_data.get("EnumOptionId", [])
            if isinstance(enum_list, list):
                return [e.get("id", "") if isinstance(e, dict) else str(e) for e in enum_list]
            if isinstance(enum_list, dict):
                return [enum_list.get("id", "")]
        return []

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Workitem):
            return NotImplemented
        return self._id == other._id and self._project.id == other._project.id

    def __repr__(self) -> str:
        return f"{self._id}: {self._truncate(self.title)}"

    __str__ = __repr__


class WorkitemCreator(Creator):
    def create_from_uri(self, polarion: Polarion, project: Project, uri: str) -> Workitem:
        return Workitem(polarion, project, None, uri)
