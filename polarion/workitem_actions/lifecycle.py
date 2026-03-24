"""Lifecycle/persistence helpers for Workitem."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..exceptions import PolarionApiError
from ..soap.envelope import NIL

if TYPE_CHECKING:
    from ..document import Document
    from ..workitem import Workitem


class WorkitemLifecycleMixin:
    def get_revision(self) -> int:
        """Get the revision number of this work item."""
        try:
            history = self._polarion._soap.call("Tracker", "getRevisions", workitemURI=self.uri)
            if isinstance(history, list) and history:
                return int(history[-1])
        except (PolarionApiError, TypeError, ValueError) as e:
            raise PolarionApiError("Could not get revision") from e
        raise PolarionApiError("Could not get revision")

    def delete(self) -> None:
        """Delete this work item from Polarion."""
        self._polarion._soap.call("Tracker", "deleteWorkItem", workitemURI=self.uri)

    def move_to_document(self, document: Document, parent: Workitem | None) -> None:
        """Move this work item into a document.

        :param document: Target document
        :param parent: Parent work item (None for top-level)
        """
        parent_uri = parent.uri if parent is not None else NIL
        self._polarion._soap.call(
            "Tracker",
            "moveWorkItemToDocument",
            workitemURI=self.uri,
            documentURI=document.uri,
            parentURI=parent_uri,
            position=-1,
            retainFlow=False,
        )

    def save(self) -> None:
        """Save changes to Polarion. Deferred if inside a batch() context."""
        if self._batch_save:
            return

        changed = self._collect_changes(self, self._polarion_data, self._original_data)
        if changed:
            changed["uri"] = self.uri
            self._polarion._soap.call("Tracker", "updateWorkItem", content=changed)
            self._reload_from_polarion()

    def _reload_from_polarion(self) -> None:
        self._polarion_data = self._polarion._soap.call(
            "Tracker", "getWorkItemByUri", uri=self._polarion_data.get("uri", self._uri)
        )
        self._build_from_polarion()
