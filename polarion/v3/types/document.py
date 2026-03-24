from dataclasses import dataclass

from .common import EnumRef


@dataclass(frozen=True)
class Document:
    uri: str
    project_id: str
    location: str
    name: str
    title: str
    status: EnumRef | None
    type: EnumRef | None


@dataclass
class DocumentCreate:
    location: str
    name: str
    title: str
    allowed_workitem_types: list[str]
    structure_link_role: str
    home_page_content: str = ""
