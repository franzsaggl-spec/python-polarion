from __future__ import annotations

from ..parser.document import parse_document, parse_document_list
from ..parser.workitem import parse_workitem_detail, parse_workitem_summary_list
from ..types.common import Page
from ..types.document import Document, DocumentCreate
from ..types.workitem import WorkitemDetail, WorkitemSummary
from .base import ServiceBase


class DocumentsService(ServiceBase):
    def get(self, project_id: str, *, uri: str | None = None, location: str | None = None) -> Document:
        if uri:
            raw = self.transport.call("Tracker", "getModuleByUri", uri=uri)
        elif location:
            raw = self.transport.call("Tracker", "getModuleByLocation", projectId=project_id, location=location)
        else:
            raise ValueError("Either uri or location is required")
        return parse_document(raw)

    def create(self, project_id: str, payload: DocumentCreate) -> Document:
        raw = self.transport.call(
            "Tracker",
            "createDocument",
            projectId=project_id,
            location=payload.location,
            name=payload.name,
            title=payload.title,
            allowedWorkItemTypes=payload.allowed_workitem_types,
            structureLinkRole=payload.structure_link_role,
            homePageContent=payload.home_page_content,
        )
        return parse_document(raw)

    def delete(self, project_id: str, uri: str) -> None:
        self.transport.call("Tracker", "deleteModule", projectId=project_id, uri=uri)

    def save(self, doc: Document) -> Document:
        raw = self.transport.call("Tracker", "updateModule", uri=doc.uri, title=doc.title)
        return parse_document(raw)

    def list_spaces(self, project_id: str) -> list[str]:
        raw = self.transport.call("Tracker", "getDocumentSpaces", projectId=project_id)
        return [str(x) for x in raw] if isinstance(raw, list) else []

    def list_locations(self, project_id: str) -> list[str]:
        raw = self.transport.call("Tracker", "getDocumentLocations", projectId=project_id)
        return [str(x) for x in raw] if isinstance(raw, list) else []

    def list_in_space(self, project_id: str, space: str, *, offset: int = 0, limit: int = 100) -> Page[Document]:
        raw = self.transport.call("Tracker", "getModules", projectId=project_id, space=space)
        items = parse_document_list(raw)
        sliced = items[offset : offset + limit]
        return Page(
            items=sliced, total=len(items), offset=offset, limit=limit, has_more=offset + len(sliced) < len(items)
        )

    def workitems(self, project_id: str, document_uri: str) -> Page[WorkitemSummary]:
        raw = self.transport.call("Tracker", "getModuleWorkItems", projectId=project_id, uri=document_uri)
        items = parse_workitem_summary_list(raw)
        return Page(items=items, total=len(items), offset=0, limit=len(items), has_more=False)

    def top_level_workitem(self, project_id: str, document_uri: str) -> WorkitemDetail:
        page = self.workitems(project_id, document_uri)
        if not page.items:
            raise ValueError("No workitems found in document")
        # Try detailed lookup by id for canonical detail payload.
        first = page.items[0]
        raw = self.transport.call("Tracker", "getWorkItemById", projectId=project_id, id=first.id)
        return parse_workitem_detail(raw)

    def children(self, project_id: str, document_uri: str, workitem_id: str) -> list[WorkitemDetail]:
        page = self.workitems(project_id, document_uri)
        details: dict[str, WorkitemDetail] = {}
        for wi in page.items:
            raw = self.transport.call("Tracker", "getWorkItemById", projectId=project_id, id=wi.id)
            details[wi.id] = parse_workitem_detail(raw)

        result: list[WorkitemDetail] = []
        for wi in details.values():
            for link in wi.links:
                target_id = link.target_id or link.target_uri.split("/")[-1]
                if wi.id == workitem_id and target_id in details:
                    result.append(details[target_id])
        return result

    def parent(self, project_id: str, document_uri: str, workitem_id: str) -> WorkitemDetail | None:
        page = self.workitems(project_id, document_uri)
        details: dict[str, WorkitemDetail] = {}
        for wi in page.items:
            raw = self.transport.call("Tracker", "getWorkItemById", projectId=project_id, id=wi.id)
            details[wi.id] = parse_workitem_detail(raw)

        for wi in details.values():
            for link in wi.links:
                target_id = link.target_id or link.target_uri.split("/")[-1]
                if target_id == workitem_id:
                    return wi
        return None

    def export_pdf(self, project_id: str, document_uri: str) -> bytes:
        raw = self.transport.call("Tracker", "exportDocumentToPDF", projectId=project_id, uri=document_uri)
        if isinstance(raw, bytes):
            return raw
        if isinstance(raw, str):
            return raw.encode()
        return b""

    def reuse(
        self,
        project_id: str,
        document_uri: str,
        *,
        target_project_id: str,
        target_location: str,
        target_name: str,
        target_title: str,
        link_role: str | None = "derived_from",
        derived_fields: list[str] | None = None,
    ) -> Document:
        raw = self.transport.call(
            "Tracker",
            "createDocumentFromModule",
            projectId=project_id,
            uri=document_uri,
            targetProjectId=target_project_id,
            targetLocation=target_location,
            targetName=target_name,
            targetTitle=target_title,
            linkRole=link_role,
            derivedFields=derived_fields or [],
        )
        return parse_document(raw)
