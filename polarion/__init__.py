"""Polarion API client for Python."""

from .client import Polarion
from .document import Document, DocumentCreator
from .factory import register_creator
from .plan import Plan, PlanCreator
from .project import Project
from .record import Record
from .testrun import Testrun, TestrunCreator
from .types import (
    Approval,
    AttachmentInfo,
    CustomFieldValue,
    EnumOption,
    HyperlinkInfo,
    LinkedItem,
    PdfProperties,
    TestStep,
    TestStepResult,
    TextContent,
)
from .user import User, UserCreator
from .workitem import Workitem, WorkitemCreator

register_creator("workitem", WorkitemCreator)
register_creator("testrun", TestrunCreator)
register_creator("user", UserCreator)
register_creator("module", DocumentCreator)
register_creator("plan", PlanCreator)

__all__ = [
    "Polarion",
    "Project",
    "Workitem",
    "Document",
    "Testrun",
    "Record",
    "Plan",
    "User",
    "TextContent",
    "EnumOption",
    "LinkedItem",
    "Approval",
    "CustomFieldValue",
    "AttachmentInfo",
    "HyperlinkInfo",
    "TestStep",
    "TestStepResult",
    "PdfProperties",
]
