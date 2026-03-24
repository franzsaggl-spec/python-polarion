"""Workitem/search-related project behavior mixin."""

from __future__ import annotations

import logging
from typing import Any

from ..exceptions import PolarionApiError, PolarionFieldError, PolarionNotFoundError
from ..utils import ensure_dict, ensure_list
from ..workitem import Workitem

logger = logging.getLogger(__name__)


class ProjectWorkitemsMixin:
    def get_workitem(self, id: str) -> Workitem:
        """Get a work item by ID.

        :param id: Work item ID (e.g. "REQ-123")
        """
        return Workitem(self.polarion, self, id)

    def create_workitem(self, workitem_type: str, fields: dict[str, Any] | None = None) -> Workitem:
        """Create a new work item.

        :param workitem_type: Work item type (e.g. "requirement")
        :param fields: Optional fields to set
        """
        return Workitem(self.polarion, self, new_workitem_type=workitem_type, new_workitem_fields=fields)

    def search_workitems(
        self,
        query: str = "",
        order: str = "Created",
        field_list: list[str] | None = None,
        limit: int = 100,
    ) -> list[Any]:
        """Search for work items (returns raw dicts, not Workitem objects).

        For full Workitem objects, use search_workitems_full().

        :param query: Polarion query string
        :param order: Sort field
        :param field_list: Fields to retrieve (default: ["id"])
        :param limit: Maximum results (-1 for unlimited)
        :return: List of dicts with the requested fields
        """
        if field_list is None:
            field_list = ["id"]

        return (
            self.polarion._soap.call(
                "Tracker",
                "queryWorkItemsLimited",
                query=self._scoped_query(query),
                sort=order,
                fields=field_list,
                limit=limit,
            )
            or []
        )

    def search_workitems_full(self, query: str = "", order: str = "Created", limit: int = 100) -> list[Workitem]:
        """Search for work items and return full Workitem objects.

        :param query: Polarion query string
        :param order: Sort field
        :param limit: Maximum results (-1 for unlimited)
        """
        results = ensure_list(self.search_workitems(query, order, ["id"], limit))
        workitems = []
        for r in results:
            wi_id = ensure_dict(r).get("id") or r
            if wi_id:
                try:
                    workitems.append(Workitem(self.polarion, self, str(wi_id)))
                except (PolarionApiError, PolarionNotFoundError, PolarionFieldError) as e:
                    logger.warning("Skipping unresolvable workitem %s: %s", wi_id, e)
        return workitems

    def search_workitems_in_baseline(
        self,
        baseline_revision: str,
        query: str = "",
        sort: str = "uri",
        field_list: list[str] | None = None,
        limit: int = 100,
    ) -> list[Any]:
        """Search for work items in a baseline.

        :param baseline_revision: Baseline revision number
        :param query: Polarion query string
        :param sort: Sort field
        :param field_list: Fields to retrieve
        :param limit: Maximum results
        """
        if field_list is None:
            field_list = ["id"]

        return (
            self.polarion._soap.call(
                "Tracker",
                "queryWorkItemsInBaselineLimited",
                query=self._scoped_query(query),
                sort=sort,
                baselineRevision=baseline_revision,
                fields=field_list,
                limit=limit,
            )
            or []
        )

    def search_workitems_full_in_baseline(
        self,
        baseline_revision: str,
        query: str = "",
        sort: str = "uri",
        limit: int = 100,
    ) -> list[Workitem]:
        """Search for work items in a baseline and return full objects."""
        results = ensure_list(self.search_workitems_in_baseline(baseline_revision, query, sort, ["id"], limit))
        return [Workitem(self.polarion, self, uri=ensure_dict(r).get("uri") or str(r)) for r in results if r]

    def get_enum(self, enum_name: str) -> list[str]:
        """Get options for an enumeration.

        :param enum_name: Enum name (e.g. "requirement-status")
        """
        result = ensure_list(
            self.polarion._soap.call("Tracker", "getAllEnumOptionsForId", projectId=self.id, enumId=enum_name)
        )
        return list(dict.fromkeys(ensure_dict(a).get("id", str(a)) for a in result))

    def _scoped_query(self, query: str) -> str:
        """Add project scope to a Polarion query string."""
        return f"{query} AND project.id:{self.id}" if query else f"project.id:{self.id}"
