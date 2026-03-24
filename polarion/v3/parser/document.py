from __future__ import annotations

from ..types.common import EnumRef
from ..types.document import Document
from .common import maybe_list, require_dict


def parse_document(raw: dict) -> Document:
    d = require_dict(raw, context="document")
    project = d.get("project", {}) if isinstance(d.get("project"), dict) else {}

    status_raw = d.get("status") if isinstance(d.get("status"), dict) else None
    status = None
    if status_raw is not None:
        status = EnumRef(
            id=str(status_raw.get("id", "")),
            uri=status_raw.get("_uri"),
            name=status_raw.get("name"),
        )

    type_raw = d.get("type") if isinstance(d.get("type"), dict) else None
    dtype = None
    if type_raw is not None:
        dtype = EnumRef(
            id=str(type_raw.get("id", "")),
            uri=type_raw.get("_uri"),
            name=type_raw.get("name"),
        )

    return Document(
        uri=str(d.get("_uri") or d.get("uri") or ""),
        project_id=str(project.get("id", "")),
        location=str(d.get("moduleLocation") or d.get("location") or ""),
        name=str(d.get("moduleName") or d.get("name") or ""),
        title=str(d.get("title") or ""),
        status=status,
        type=dtype,
    )


def parse_document_list(raw: object) -> list[Document]:
    return [parse_document(d) for d in maybe_list(raw) if isinstance(d, dict)]
