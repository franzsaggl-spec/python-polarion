"""Document-related project behavior mixin."""

from __future__ import annotations

from ..document import Document
from ..utils import ensure_str_list


class ProjectDocumentsMixin:
    def get_document(self, location: str) -> Document:
        """Get a document by location.

        :param location: Document location path
        """
        return Document(self.polarion, self, location=location)

    def create_document(
        self,
        location: str,
        name: str,
        title: str,
        allowed_workitem_types: list[str],
        structure_link_role: str,
        home_page_content: str = "",
    ) -> Document:
        """Create a new document.

        :param location: Document location (e.g. "_default")
        :param name: Document name
        :param title: Document title
        :param allowed_workitem_types: List of allowed work item types
        :param structure_link_role: Link role for document hierarchy
        :param home_page_content: Initial HTML content
        """
        type_ids = [{"id": t} for t in allowed_workitem_types]
        role_id = {"id": structure_link_role}
        uri = self.polarion._soap.call(
            "Tracker",
            "createDocument",
            projectId=self.id,
            location=location,
            documentName=name,
            documentTitle=title,
            allowedWITypes=type_ids,
            structureLinkRole=role_id,
            homePageContent=home_page_content,
        )
        return Document(self.polarion, self, uri=uri)

    def get_document_spaces(self) -> list[str]:
        """Get all document spaces."""
        result = self.polarion._soap.call("Tracker", "getDocumentSpaces", projectId=self.id)
        return sorted(ensure_str_list(result))

    def get_document_locations(self) -> list[str]:
        """Get all document locations."""
        result = self.polarion._soap.call("Tracker", "getDocumentLocations", projectId=self.id)
        return sorted(ensure_str_list(result))

    def get_documents_in_space(self, space: str) -> list[Document]:
        """Get all documents in a space.

        :param space: Space name
        """
        uris = self.polarion._soap.call("Tracker", "getModuleUris", projectId=self.id, spaceId=space)
        if not isinstance(uris, list):
            return []
        return [Document(self.polarion, self, uri=u) for u in uris]
