"""Polarion Document model."""

from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING, Any

from .base.custom_fields import CustomFields
from .exceptions import PolarionNotFoundError
from .factory import Creator, create_from_uri
from .soap.envelope import NIL

if TYPE_CHECKING:
    from .client import Polarion
    from .project import Project
    from .workitem import Workitem

logger = logging.getLogger(__name__)


class Document(CustomFields):
    """A Polarion document (module).

    :param polarion: Polarion client
    :param project: Project instance
    :param uri: Document URI
    :param location: Document location path
    """

    _default_summary_fields = ["moduleFolder", "title", "moduleName"]

    # Declared attributes
    title: str | None = None
    moduleName: str | None = None
    moduleFolder: str | None = None
    structureLinkRole: Any = None
    homePageContent: Any = None
    status: Any = None
    type: Any = None

    def __init__(
        self,
        polarion: Polarion,
        project: Project,
        uri: str | None = None,
        location: str | None = None,
    ) -> None:
        super().__init__(polarion, project, uri=uri)
        self._uri = uri
        self._project = project
        self._polarion = polarion
        self._polarion_data: dict[str, Any] = {}
        self._original_data: dict[str, Any] = {}

        if self._uri is not None:
            self._polarion_data = self._polarion._soap.call("Tracker", "getModuleByUri", uri=self._uri)
            if isinstance(self._polarion_data, dict) and self._polarion_data.get("unresolvable"):
                raise PolarionNotFoundError(f"Cannot find document at URI {self._uri}")

        elif location is not None:
            self._polarion_data = self._polarion._soap.call(
                "Tracker", "getModuleByLocation", projectId=self._project.id, locationPath=location
            )
            if isinstance(self._polarion_data, dict) and self._polarion_data.get("unresolvable"):
                raise PolarionNotFoundError(f"Cannot find document at location {location}")
            if isinstance(self._polarion_data, dict):
                self._uri = self._polarion_data.get("uri")

        self._build_from_polarion()

    def _build_from_polarion(self) -> None:
        if isinstance(self._polarion_data, dict) and not self._polarion_data.get("unresolvable"):
            self._original_data = copy.deepcopy(self._polarion_data)
            self._populate_from_dict(self, self._polarion_data)

    def _reload_from_polarion(self) -> None:
        self._polarion_data = self._polarion._soap.call("Tracker", "getModuleByUri", uri=self._uri)
        self._build_from_polarion()

    def export_to_pdf(self) -> bytes:
        """Export the document as PDF.

        :return: PDF content as bytes
        """
        from .types import PdfProperties

        pdf_props = PdfProperties()
        return self._polarion._soap.call(
            "Tracker", "exportDocumentToPDF", moduleURI=self._uri, pdfProperties=pdf_props.to_soap()
        )

    def get_workitem_uris(self) -> list[str]:
        """Get URIs of all work items in this document."""
        result = self._polarion._soap.call(
            "Tracker", "getModuleWorkItemUris", moduleURI=self._uri, baselineRevision=None, deep=True
        )
        return result if isinstance(result, list) else []

    def get_workitems(self) -> list[Workitem]:
        """Get all work items in this document (may be slow for large documents)."""
        workitems = []
        for uri in self.get_workitem_uris():
            try:
                workitems.append(create_from_uri(self._polarion, self._project, uri))
            except Exception as e:
                logger.warning("Skipping unresolvable workitem URI %s: %s", uri, e)
        return workitems

    def get_top_level_workitem(self) -> Workitem:
        """Get the top-level work item (usually the document title)."""
        uris = self.get_workitem_uris()
        if not uris:
            raise PolarionNotFoundError("Document has no work items")
        return create_from_uri(self._polarion, self._project, uris[0])

    def get_children(self, workitem: Workitem) -> list[Workitem]:
        """Get children of a work item within this document.

        :param workitem: Parent work item
        """
        children = []
        derived = getattr(workitem, "linkedWorkItemsDerived", None)
        if derived is not None:
            doc_uris = self.get_workitem_uris()
            items = derived if isinstance(derived, list) else [derived]
            struct_role = self.structureLinkRole
            struct_role_id = struct_role.get("id", "") if isinstance(struct_role, dict) else str(struct_role or "")
            for w in items:
                if isinstance(w, dict):
                    role = w.get("role", {})
                    role_id = role.get("id", "") if isinstance(role, dict) else str(role)
                    wi_uri = w.get("workItemURI", "")
                    if role_id == struct_role_id and wi_uri in doc_uris:
                        try:
                            children.append(create_from_uri(self._polarion, self._project, wi_uri))
                        except Exception as e:
                            logger.warning("Skipping unresolvable child workitem %s: %s", wi_uri, e)
        return children

    def get_parent(self, workitem: Workitem) -> Workitem | None:
        """Get the parent of a work item within this document.

        :param workitem: Child work item
        """
        linked = getattr(workitem, "linkedWorkItems", None)
        if linked is not None:
            doc_uris = self.get_workitem_uris()
            items = linked if isinstance(linked, list) else [linked]
            struct_role = self.structureLinkRole
            struct_role_id = struct_role.get("id", "") if isinstance(struct_role, dict) else str(struct_role or "")
            for w in items:
                if isinstance(w, dict):
                    role = w.get("role", {})
                    role_id = role.get("id", "") if isinstance(role, dict) else str(role)
                    wi_uri = w.get("workItemURI", "")
                    if role_id == struct_role_id and wi_uri in doc_uris:
                        return create_from_uri(self._polarion, self._project, wi_uri)
        return None

    def add_heading(self, title: str, parent_workitem: Workitem | None = None) -> Workitem:
        """Add a heading to the document.

        :param title: Heading title
        :param parent_workitem: Parent work item (None for top-level)
        """
        heading = self._project.create_workitem("heading")
        heading.title = title
        heading.save()
        heading.move_to_document(self, parent_workitem)
        return heading

    def is_custom_field_allowed(self, _: str) -> bool:
        """Documents allow all custom fields."""
        return True

    def reuse(
        self,
        target_project_id: str,
        target_location: str,
        target_name: str,
        target_title: str,
        link_role: str | None = "derived_from",
        derived_fields: list[str] | None = None,
    ) -> Document:
        """Reuse this document in another project.

        :param target_project_id: Target project ID
        :param target_location: Target document location
        :param target_name: Target document name
        :param target_title: Target document title
        :param link_role: Link role for derived documents (None for no linking)
        :param derived_fields: Fields to derive in target
        """
        if derived_fields is None and link_role is not None:
            derived_fields = ["title", "description"]
        new_uri = self._polarion._soap.call(
            "Tracker",
            "reuseDocument",
            moduleURI=self._uri,
            targetProjectId=target_project_id,
            targetLocation=target_location,
            targetModuleName=target_name,
            targetModuleTitle=target_title,
            copyWorkItems=True,
            linkRole=link_role,
            derivedFields=derived_fields,
        )
        return create_from_uri(self._polarion, self._project, new_uri)

    def update_derived(self, revision: str | None = None, auto_suspect: bool = False) -> None:
        """Update a reused document to a revision of the source.

        :param revision: Source document revision (None for latest)
        :param auto_suspect: Mark changed links as suspect
        """
        self._polarion._soap.call(
            "Tracker",
            "updateDerivedDocument",
            moduleURI=self._uri,
            revision=revision if revision is not None else NIL,
            autoSuspect=auto_suspect,
        )

    def save(self) -> None:
        """Save document changes to Polarion."""
        changed: dict[str, Any] = {}
        for key in self._polarion_data:
            if key in ("uri", "unresolvable"):
                continue
            current_val = getattr(self, key, None)
            if current_val is not None and current_val != self._original_data.get(key):
                changed[key] = current_val
        if changed:
            changed["uri"] = self._uri
            self._polarion._soap.call("Tracker", "updateModule", content=changed)
            self._reload_from_polarion()

    def delete(self) -> None:
        """Delete this document from Polarion."""
        self._polarion._soap.call("Tracker", "deleteModule", moduleURI=self.uri)

    def __repr__(self) -> str:
        return f"Polarion document {self._truncate(self.title)} in {self.moduleFolder}"

    __str__ = __repr__


class DocumentCreator(Creator):
    def create_from_uri(self, polarion: Polarion, project: Project, uri: str) -> Document:
        return Document(polarion, project, uri)
