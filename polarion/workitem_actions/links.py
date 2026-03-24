"""Description and linked item helpers for Workitem."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ..exceptions import PolarionApiError, PolarionFieldError, PolarionNotFoundError
from ..factory import create_from_uri
from ..utils import ensure_list, extract_id

if TYPE_CHECKING:
    from ..workitem import Workitem

logger = logging.getLogger(__name__)


class WorkitemLinkMixin:
    def get_description(self) -> str | None:
        """Get the description content (may contain HTML)."""
        if self.description is not None and isinstance(self.description, dict):
            return self.description.get("content")
        return None

    def add_hyperlink(self, url: str, hyperlink_type: Any) -> None:
        """Add a hyperlink to this work item.

        :param url: The URL
        :param hyperlink_type: Link type (use HyperlinkRoles enum or string)
        """
        if hasattr(hyperlink_type, "value"):
            hyperlink_type = hyperlink_type.value
        self._polarion._soap.call("Tracker", "addHyperlink", workitemURI=self.uri, url=url, role={"id": hyperlink_type})
        self._reload_from_polarion()

    def remove_hyperlink(self, url: str) -> None:
        """Remove a hyperlink from this work item."""
        self._polarion._soap.call("Tracker", "removeHyperlink", workitemURI=self.uri, url=url)
        self._reload_from_polarion()

    def add_linked_item(self, workitem: Workitem, link_type: str) -> None:
        """Add a link to another work item.

        :param workitem: Target work item
        :param link_type: Link role type
        """
        self._polarion._soap.call(
            "Tracker", "addLinkedItem", workitemURI=self.uri, linkedWorkitemURI=workitem.uri, role={"id": link_type}
        )
        self._reload_from_polarion()
        workitem._reload_from_polarion()

    def remove_linked_item(self, workitem: Workitem, role: str | None = None) -> None:
        """Remove a linked work item.

        :param workitem: Work item to unlink
        :param role: Specific role to remove. If None, removes all links to this item.
        """
        if role is not None:
            self._polarion._soap.call(
                "Tracker", "removeLinkedItem", workitemURI=self.uri, linkedWorkitemURI=workitem.uri, role={"id": role}
            )
        else:
            for li in ensure_list(self.linkedWorkItems):
                if isinstance(li, dict) and li.get("workItemURI") == workitem.uri:
                    self._polarion._soap.call(
                        "Tracker",
                        "removeLinkedItem",
                        workitemURI=self.uri,
                        linkedWorkitemURI=li["workItemURI"],
                        role=li.get("role", {}),
                    )
            for li in ensure_list(self.linkedWorkItemsDerived):
                if isinstance(li, dict) and li.get("workItemURI") == workitem.uri:
                    self._polarion._soap.call(
                        "Tracker",
                        "removeLinkedItem",
                        workitemURI=li["workItemURI"],
                        linkedWorkitemURI=self.uri,
                        role=li.get("role", {}),
                    )
        self._reload_from_polarion()
        workitem._reload_from_polarion()

    def get_linked_items_with_roles(self) -> list[tuple[str, Workitem]]:
        """Get linked work items with their link roles.

        :return: List of (role, Workitem) tuples
        """
        linked: list[tuple[str, Workitem]] = []
        for attr_name in ("linkedWorkItems", "linkedWorkItemsDerived"):
            for li in ensure_list(getattr(self, attr_name, None)):
                if isinstance(li, dict):
                    try:
                        linked.append(
                            (
                                extract_id(li.get("role", {})),
                                create_from_uri(self._polarion, self._project, li["workItemURI"]),
                            )
                        )
                    except (PolarionApiError, PolarionNotFoundError, PolarionFieldError) as e:
                        logger.warning("Skipping unresolvable linked item %s: %s", li.get("workItemURI"), e)
        return linked

    def get_linked_items(self) -> list[Workitem]:
        """Get all linked work items (without roles)."""
        return [item for _, item in self.get_linked_items_with_roles()]
