from __future__ import annotations

from ..types.common import Page
from ..types.document import Document, DocumentCreate
from ..types.workitem import WorkitemDetail, WorkitemSummary
from .base import ServiceBase


class DocumentsService(ServiceBase):
    def get(self, project_id: str, *, uri: str | None = None, location: str | None = None) -> Document:
        raise NotImplementedError

    def create(self, project_id: str, payload: DocumentCreate) -> Document:
        raise NotImplementedError

    def delete(self, project_id: str, uri: str) -> None:
        raise NotImplementedError

    def save(self, doc: Document) -> Document:
        raise NotImplementedError

    def list_spaces(self, project_id: str) -> list[str]:
        raise NotImplementedError

    def list_locations(self, project_id: str) -> list[str]:
        raise NotImplementedError

    def list_in_space(self, project_id: str, space: str, *, offset: int = 0, limit: int = 100) -> Page[Document]:
        raise NotImplementedError

    def workitems(self, project_id: str, document_uri: str) -> Page[WorkitemSummary]:
        raise NotImplementedError

    def top_level_workitem(self, project_id: str, document_uri: str) -> WorkitemDetail:
        raise NotImplementedError

    def children(self, project_id: str, document_uri: str, workitem_id: str) -> list[WorkitemDetail]:
        raise NotImplementedError

    def parent(self, project_id: str, document_uri: str, workitem_id: str) -> WorkitemDetail | None:
        raise NotImplementedError

    def export_pdf(self, project_id: str, document_uri: str) -> bytes:
        raise NotImplementedError

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
        raise NotImplementedError
