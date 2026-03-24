"""Polarion Project model."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .document import Document
from .exceptions import PolarionNotFoundError
from .factory import create_from_uri
from .plan import Plan
from .testrun import Testrun
from .user import User
from .workitem import Workitem

if TYPE_CHECKING:
    from .client import Polarion

logger = logging.getLogger(__name__)


class Project:
    """A Polarion project.

    :param polarion: Polarion client instance
    :param project_id: The project ID (as in the Polarion URL)
    """

    def __init__(self, polarion: Polarion, project_id: str) -> None:
        self.polarion = polarion
        self.id = project_id

        try:
            self.polarion_data = self.polarion._soap.call("Project", "getProject", projectId=self.id)
        except Exception as e:
            raise PolarionNotFoundError(f"Could not find project {project_id}") from e

        if isinstance(self.polarion_data, dict) and not self.polarion_data.get("unresolvable"):
            self.name = self.polarion_data.get("name", "")
            self.tracker_prefix = self.polarion_data.get("trackerPrefix", "")
        else:
            raise PolarionNotFoundError(f"Could not find project {project_id}")

    # --- Users ---

    def get_users(self) -> list[User]:
        """Get all users in this project."""
        users: list[User] = []
        project_users = self.polarion._soap.call("Project", "getProjectUsers", projectId=self.id)
        if not isinstance(project_users, list):
            return users
        for user_data in project_users:
            try:
                users.append(User(self.polarion, user_data))
            except Exception as e:
                name = user_data.get("name", "unknown") if isinstance(user_data, dict) else "unknown"
                logger.warning("Could not retrieve %s: %s", name, e)
        return users

    def find_user(self, name: str) -> User | None:
        """Find a user by ID or name.

        :param name: User ID or display name (case-insensitive)
        """
        for user in self.get_users():
            if user.id.lower() == name.lower() or user.name.lower() == name.lower():
                return user
        return None

    # --- Work Items ---

    def get_workitem(self, id: str) -> Workitem:
        """Get a work item by ID.

        :param id: Work item ID (e.g. "REQ-123")
        """
        return Workitem(self.polarion, self, id)

    def create_workitem(self, workitem_type: str, fields: dict[str, Any] | None = None) -> Workitem:
        """Create a new work item.

        :param workitem_type: Work item type (e.g. "requirement")
        :param fields: Optional fields to set
        """
        return Workitem(self.polarion, self, new_workitem_type=workitem_type, new_workitem_fields=fields)

    def search_workitems(
        self,
        query: str = "",
        order: str = "Created",
        field_list: list[str] | None = None,
        limit: int = 100,
    ) -> list[Any]:
        """Search for work items (returns lightweight results).

        For full Workitem objects, use search_workitems_full().

        :param query: Polarion query string
        :param order: Sort field
        :param field_list: Fields to retrieve (default: ["id"])
        :param limit: Maximum results (-1 for unlimited)
        """
        if field_list is None:
            field_list = ["id"]

        full_query = f"{query} AND project.id:{self.id}" if query else f"project.id:{self.id}"
        return (
            self.polarion._soap.call(
                "Tracker", "queryWorkItemsLimited", query=full_query, sort=order, fields=field_list, limit=limit
            )
            or []
        )

    def search_workitems_full(self, query: str = "", order: str = "Created", limit: int = 100) -> list[Workitem]:
        """Search for work items and return full Workitem objects.

        :param query: Polarion query string
        :param order: Sort field
        :param limit: Maximum results (-1 for unlimited)
        """
        results = self.search_workitems(query, order, ["id"], limit)
        if not isinstance(results, list):
            return []
        workitems = []
        for r in results:
            wi_id = r.get("id") if isinstance(r, dict) else r
            if wi_id:
                try:
                    workitems.append(Workitem(self.polarion, self, str(wi_id)))
                except Exception:
                    pass
        return workitems

    def search_workitems_in_baseline(
        self,
        baseline_revision: str,
        query: str = "",
        sort: str = "uri",
        field_list: list[str] | None = None,
        limit: int = 100,
    ) -> list[Any]:
        """Search for work items in a baseline.

        :param baseline_revision: Baseline revision number
        :param query: Polarion query string
        :param sort: Sort field
        :param field_list: Fields to retrieve
        :param limit: Maximum results
        """
        if field_list is None:
            field_list = ["id"]

        full_query = f"{query} AND project.id:{self.id}" if query else f"project.id:{self.id}"
        return (
            self.polarion._soap.call(
                "Tracker",
                "queryWorkItemsInBaselineLimited",
                query=full_query,
                sort=sort,
                baselineRevision=baseline_revision,
                fields=field_list,
                limit=limit,
            )
            or []
        )

    def search_workitems_full_in_baseline(
        self,
        baseline_revision: str,
        query: str = "",
        sort: str = "uri",
        limit: int = 100,
    ) -> list[Workitem]:
        """Search for work items in a baseline and return full objects."""
        results = self.search_workitems_in_baseline(baseline_revision, query, sort, ["id"], limit)
        if not isinstance(results, list):
            return []
        return [
            Workitem(self.polarion, self, uri=r.get("uri") if isinstance(r, dict) else str(r)) for r in results if r
        ]

    # --- Enumerations ---

    def get_enum(self, enum_name: str) -> list[str]:
        """Get options for an enumeration.

        :param enum_name: Enum name (e.g. "requirement-status")
        """
        result = self.polarion._soap.call("Tracker", "getAllEnumOptionsForId", projectId=self.id, enumId=enum_name)
        if isinstance(result, list):
            return list(dict.fromkeys(a.get("id", "") if isinstance(a, dict) else str(a) for a in result))
        return []

    # --- Test Runs ---

    def get_test_run(self, id: str) -> Testrun:
        """Get a test run by ID.

        :param id: Test run ID
        """
        uri = f"subterra:data-service:objects:/default/{self.id}${{TestRun}}{id}"
        return Testrun(self.polarion, uri=uri)

    def search_test_runs(self, query: str = "", order: str = "Created", limit: int = 100) -> list[Testrun]:
        """Search for test runs.

        :param query: Polarion query
        :param order: Sort field
        :param limit: Maximum results
        """
        full_query = f"{query} AND project.id:{self.id}" if query else f"project.id:{self.id}"
        results = self.polarion._soap.call(
            "TestManagement", "searchTestRunsLimited", query=full_query, sort=order, limit=limit
        )
        if not isinstance(results, list):
            return []
        return [Testrun(self.polarion, polarion_test_run=tr) for tr in results if tr]

    def create_test_run(self, id: str, title: str, template_id: str) -> Testrun:
        """Create a new test run from a template.

        :param id: New test run ID
        :param title: Test run title
        :param template_id: Template test run ID
        """
        new_uri = self.polarion._soap.call(
            "TestManagement",
            "createTestRunWithTitle",
            projectId=self.id,
            testRunId=id,
            title=title,
            templateId=template_id,
        )
        return create_from_uri(self.polarion, self, new_uri)

    # --- Plans ---

    def get_plan(self, id: str) -> Plan:
        """Get a plan by ID."""
        return Plan(self.polarion, self, id=id)

    def create_plan(
        self,
        name: str,
        plan_id: str,
        template: str,
        parent: Plan | None = None,
    ) -> Plan:
        """Create a new plan.

        :param name: Plan name
        :param plan_id: Plan ID
        :param template: Template name ("release", "iteration", etc.)
        :param parent: Optional parent plan
        """
        return Plan(
            self.polarion,
            self,
            new_plan_name=name,
            new_plan_id=plan_id,
            new_plan_template=template,
            new_plan_parent=parent,
        )

    def search_plans(self, query: str = "", order: str = "Created", limit: int = 100) -> list[Any]:
        """Search for plans (lightweight results).

        :param query: Polarion query
        :param order: Sort field
        :param limit: Maximum results
        """
        full_query = f"{query} AND project.id:{self.id}" if query else f"project.id:{self.id}"
        return self.polarion._soap.call("Planning", "searchPlans", query=full_query, sort=order, limit=limit) or []

    def search_plans_full(self, query: str = "", order: str = "Created", limit: int = 100) -> list[Plan]:
        """Search for plans and return full Plan objects."""
        return [Plan(self.polarion, self, polarion_record=p) for p in self.search_plans(query, order, limit)]

    # --- Documents ---

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
        if isinstance(result, list):
            return sorted(result)
        return []

    def get_document_locations(self) -> list[str]:
        """Get all document locations."""
        result = self.polarion._soap.call("Tracker", "getDocumentLocations", projectId=self.id)
        if isinstance(result, list):
            return sorted(result)
        return []

    def get_documents_in_space(self, space: str) -> list[Document]:
        """Get all documents in a space.

        :param space: Space name
        """
        uris = self.polarion._soap.call("Tracker", "getModuleUris", projectId=self.id, spaceId=space)
        if not isinstance(uris, list):
            return []
        return [Document(self.polarion, self, uri=u) for u in uris]

    def __repr__(self) -> str:
        return f"Polarion project {self.name} prefix {self.tracker_prefix}"

    __str__ = __repr__
