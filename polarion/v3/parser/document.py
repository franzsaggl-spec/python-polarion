from __future__ import annotations

from ..types.document import Document
from .common import maybe_list, require_dict


def parse_document(raw: dict) -> Document:
    d = require_dict(raw, context="document")
    project = d.get("project", {}) if isinstance(d.get("project"), dict) else {}
    status = d.get("status") if isinstance(d.get("status"), dict) else None
    dtype = d.get("type") if isinstance(d.get("type"), dict) else None
    return Document(
        uri=str(d.get("_uri") or d.get("uri") or ""),
        project_id=str(project.get("id", "")),
        location=str(d.get("moduleLocation") or d.get("location") or ""),
        name=str(d.get("moduleName") or d.get("name") or ""),
        title=str(d.get("title") or ""),
        status=None if status is None else status,
        type=None if dtype is None else dtype,
    )


def parse_document_list(raw: object) -> list[Document]:
    return [parse_document(d) for d in maybe_list(raw) if isinstance(d, dict)]
