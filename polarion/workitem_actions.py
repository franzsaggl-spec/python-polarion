"""Behavior mixin for Polarion Workitem operations."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

from .exceptions import PolarionApiError, PolarionFieldError, PolarionNotFoundError
from .soap.envelope import NIL
from .types import TextContent
from .user import User
from .utils import ensure_dict, ensure_list, extract_id

if TYPE_CHECKING:
    from .document import Document
    from .workitem import Workitem

logger = logging.getLogger(__name__)


class WorkitemActionsMixin:
    def get_author(self) -> User | None:
        """Get the author of this work item."""
        if self.author is not None:
            return User(self._polarion, self.author if isinstance(self.author, dict) else {"id": self.author})
        return None

    def get_approver_users(self) -> list[User]:
        """Get the list of approver users."""
        approval_list = ensure_list(self.approvals)
        users = []
        for a in approval_list:
            a_data = ensure_dict(a)
            if a_data:
                user_data = ensure_dict(a_data.get("user")) or {"id": a_data.get("user")}
                try:
                    users.append(User(self._polarion, user_data))
                except (PolarionApiError, PolarionNotFoundError, PolarionFieldError) as e:
                    logger.warning("Skipping unresolvable approver user %s: %s", user_data, e)
        return users

    def add_approvee(self, user: User, remove_others: bool = False) -> None:
        """Add a user as an approvee.

        :param user: User to add
        :param remove_others: If True, remove all other approvees first
        """
        if remove_others:
            for current_user in self.get_approver_users():
                self._polarion._soap.call("Tracker", "removeApprovee", workitemURI=self.uri, userId=current_user.id)

        self._polarion._soap.call("Tracker", "addApprovee", workitemURI=self.uri, userId=user.id)
        self._reload_from_polarion()

    def remove_approvee(self, user: User) -> None:
        """Remove a user from approvees."""
        self._polarion._soap.call("Tracker", "removeApprovee", workitemURI=self.uri, userId=user.id)
        self._reload_from_polarion()

    def get_assigned_users(self) -> list[User]:
        """Get the list of assigned users."""
        user_list = ensure_list(self.assignee)
        users = []
        for u in user_list:
            try:
                users.append(User(self._polarion, u if isinstance(u, dict) else {"id": u}))
            except (PolarionApiError, PolarionNotFoundError, PolarionFieldError) as e:
                logger.warning("Skipping unresolvable assigned user %s: %s", u, e)
        return users

    def add_assignee(self, user: User, remove_others: bool = False) -> None:
        """Add a user as an assignee.

        :param user: User to add
        :param remove_others: If True, remove all other assignees first
        """
        if remove_others:
            for current_user in self.get_assigned_users():
                self._polarion._soap.call("Tracker", "removeAssignee", workitemURI=self.uri, userId=current_user.id)

        self._polarion._soap.call("Tracker", "addAssignee", workitemURI=self.uri, userId=user.id)
        self._reload_from_polarion()

    def remove_assignee(self, user: User) -> None:
        """Remove a user from assignees."""
        self._polarion._soap.call("Tracker", "removeAssignee", workitemURI=self.uri, userId=user.id)
        self._reload_from_polarion()

    def _get_enum(self, suffix: str) -> list[str]:
        try:
            return self._project.get_enum(f"{self.type['id'] if isinstance(self.type, dict) else self.type}-{suffix}")
        except Exception as e:
            # Keep enum lookup failure non-fatal for compatibility with partial/mocked backends.
            logger.warning("Could not get %s enum: %s", suffix, e)
            return []

    def get_status_enum(self) -> list[str]:
        """Get the status enum for this work item type."""
        return self._get_enum("status")

    def get_resolution_enum(self) -> list[str]:
        """Get the resolution enum for this work item type."""
        return self._get_enum("resolution")

    def get_severity_enum(self) -> list[str]:
        """Get the severity enum for this work item type."""
        return self._get_enum("severity")

    def get_allowed_custom_keys(self) -> list[str]:
        """Get allowed custom field keys for this work item."""
        try:
            result = self._polarion._soap.call("Tracker", "getCustomFieldKeys", workitemURI=self.uri)
            return result if isinstance(result, list) else []
        except PolarionApiError as e:
            logger.warning("Could not get custom field keys: %s", e)
            return []

    def is_custom_field_allowed(self, key: str) -> bool:
        """Check if a custom field key is allowed."""
        return key in self.get_allowed_custom_keys()

    def get_available_statuses(self) -> list[str]:
        """Get available status transitions for this work item."""
        result = self._polarion._soap.call(
            "Tracker", "getAvailableEnumOptionIdsForId", workitemURI=self.uri, enumId="status"
        )
        if isinstance(result, list):
            return [s.get("id", "") if isinstance(s, dict) else str(s) for s in result]
        return []

    def get_available_actions(self) -> list[str]:
        """Get available workflow action names."""
        result = self._polarion._soap.call("Tracker", "getAvailableActions", workitemURI=self.uri)
        if isinstance(result, list):
            return [a.get("nativeActionId", "") if isinstance(a, dict) else str(a) for a in result]
        return []

    def get_available_actions_details(self) -> list[dict[str, Any]]:
        """Get available workflow actions with full details."""
        result = self._polarion._soap.call("Tracker", "getAvailableActions", workitemURI=self.uri)
        if isinstance(result, list):
            return result
        return []

    def perform_action(self, action_name: str) -> None:
        """Perform a workflow action by name.

        :param action_name: Action name or native action ID
        :raises PolarionFieldError: If the action is not available
        """
        actions = self._polarion._soap.call("Tracker", "getAvailableActions", workitemURI=self.uri)
        if isinstance(actions, list):
            for action in actions:
                if isinstance(action, dict):
                    if action.get("nativeActionId") == action_name or action.get("actionName") == action_name:
                        self._polarion._soap.call(
                            "Tracker", "performWorkflowAction", workitemURI=self.uri, actionId=action["actionId"]
                        )
                        return
        available = []
        if isinstance(actions, list):
            available = [a.get("nativeActionId", "") for a in actions if isinstance(a, dict)]
        raise PolarionFieldError(f"Action '{action_name}' not available. Available: {available}")

    def perform_action_id(self, action_id: int) -> None:
        """Perform a workflow action by ID."""
        self._polarion._soap.call("Tracker", "performWorkflowAction", workitemURI=self.uri, actionId=action_id)

    def get_description(self) -> str | None:
        """Get the description content (may contain HTML)."""
        if self.description is not None and isinstance(self.description, dict):
            return self.description.get("content")
        return None

    def add_hyperlink(self, url: str, hyperlink_type: Any) -> None:
        """Add a hyperlink to this work item.

        :param url: The URL
        :param hyperlink_type: Link type (use HyperlinkRoles enum or string)
        """
        if hasattr(hyperlink_type, "value"):
            hyperlink_type = hyperlink_type.value
        self._polarion._soap.call("Tracker", "addHyperlink", workitemURI=self.uri, url=url, role={"id": hyperlink_type})
        self._reload_from_polarion()

    def remove_hyperlink(self, url: str) -> None:
        """Remove a hyperlink from this work item."""
        self._polarion._soap.call("Tracker", "removeHyperlink", workitemURI=self.uri, url=url)
        self._reload_from_polarion()

    def add_linked_item(self, workitem: Workitem, link_type: str) -> None:
        """Add a link to another work item.

        :param workitem: Target work item
        :param link_type: Link role type
        """
        self._polarion._soap.call(
            "Tracker", "addLinkedItem", workitemURI=self.uri, linkedWorkitemURI=workitem.uri, role={"id": link_type}
        )
        self._reload_from_polarion()
        workitem._reload_from_polarion()

    def remove_linked_item(self, workitem: Workitem, role: str | None = None) -> None:
        """Remove a linked work item.

        :param workitem: Work item to unlink
        :param role: Specific role to remove. If None, removes all links to this item.
        """
        if role is not None:
            self._polarion._soap.call(
                "Tracker", "removeLinkedItem", workitemURI=self.uri, linkedWorkitemURI=workitem.uri, role={"id": role}
            )
        else:
            for li in ensure_list(self.linkedWorkItems):
                if isinstance(li, dict) and li.get("workItemURI") == workitem.uri:
                    self._polarion._soap.call(
                        "Tracker",
                        "removeLinkedItem",
                        workitemURI=self.uri,
                        linkedWorkitemURI=li["workItemURI"],
                        role=li.get("role", {}),
                    )
            for li in ensure_list(self.linkedWorkItemsDerived):
                if isinstance(li, dict) and li.get("workItemURI") == workitem.uri:
                    self._polarion._soap.call(
                        "Tracker",
                        "removeLinkedItem",
                        workitemURI=li["workItemURI"],
                        linkedWorkitemURI=self.uri,
                        role=li.get("role", {}),
                    )
        self._reload_from_polarion()
        workitem._reload_from_polarion()

    def get_linked_items_with_roles(self) -> list[tuple[str, Workitem]]:
        """Get linked work items with their link roles.

        :return: List of (role, Workitem) tuples
        """
        linked: list[tuple[str, Workitem]] = []
        for attr_name in ("linkedWorkItems", "linkedWorkItemsDerived"):
            for li in ensure_list(getattr(self, attr_name, None)):
                if isinstance(li, dict):
                    try:
                        linked.append(
                            (
                                extract_id(li.get("role", {})),
                                Workitem(self._polarion, self._project, uri=li["workItemURI"]),
                            )
                        )
                    except (PolarionApiError, PolarionNotFoundError, PolarionFieldError) as e:
                        logger.warning("Skipping unresolvable linked item %s: %s", li.get("workItemURI"), e)
        return linked

    def get_linked_items(self) -> list[Workitem]:
        """Get all linked work items (without roles)."""
        return [item for _, item in self.get_linked_items_with_roles()]

    def has_attachment(self) -> bool:
        """Check if this work item has attachments."""
        return self.attachments is not None

    def get_attachment(self, attachment_id: str) -> bytes:
        """Get attachment data by ID."""
        return self._polarion._soap.call("Tracker", "getAttachment", workitemURI=self.uri, id=attachment_id)

    def save_attachment_as_file(self, attachment_id: str, file_path: str) -> None:
        """Save an attachment to a file."""
        data = self.get_attachment(attachment_id)
        with open(file_path, "wb") as f:
            f.write(data)

    def delete_attachment(self, attachment_id: str) -> None:
        """Delete an attachment."""
        self._polarion._soap.call("Tracker", "deleteAttachment", workitemURI=self.uri, id=attachment_id)
        self._reload_from_polarion()

    def add_attachment(self, file_path: str, title: str) -> None:
        """Upload a file as an attachment.

        :param file_path: Path to the file
        :param title: Attachment title
        """
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            self._polarion._soap.call(
                "Tracker", "createAttachment", workitemURI=self.uri, fileName=file_name, title=title, content=f.read()
            )
        self._reload_from_polarion()

    def update_attachment(self, attachment_id: str, file_path: str, title: str) -> None:
        """Update an existing attachment."""
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            self._polarion._soap.call(
                "Tracker",
                "updateAttachment",
                workitemURI=self.uri,
                id=attachment_id,
                fileName=file_name,
                title=title,
                content=f.read(),
            )
        self._reload_from_polarion()

    def has_test_steps(self) -> bool:
        """Check if this work item has test steps."""
        return bool(self._parsed_test_steps)

    def get_test_steps(self) -> list[dict[str, str]]:
        """Get parsed test steps."""
        return self._parsed_test_steps or []

    def get_test_step_header(self) -> list[str]:
        """Get test step column names."""
        if not self._has_test_step_field():
            raise PolarionFieldError("Work item does not have test step custom field")
        return self._get_configured_test_step_attrs("name")

    def get_test_step_header_id(self) -> list[str]:
        """Get test step column IDs."""
        if not self._has_test_step_field():
            raise PolarionFieldError("Work item does not have test step custom field")
        return self._get_configured_test_step_attrs("id")

    def add_test_step(self, *args: str) -> None:
        """Add a new test step.

        :param args: One string per test step column
        """
        if not self._has_test_step_field():
            raise PolarionFieldError("Cannot add test steps: custom field not available")

        if self._polarion_test_steps is None:
            self._polarion_test_steps = {}

        keys = self._polarion_test_steps.get("keys")
        if keys is None:
            column_ids = self._get_configured_test_step_attrs("id")
            keys = {"EnumOptionId": [{"id": kid} for kid in column_ids]}
            self._polarion_test_steps["keys"] = keys

        num_columns = len(self._extract_enum_ids(keys))
        if len(args) != num_columns:
            raise PolarionFieldError(f"Test step requires {num_columns} arguments, got {len(args)}")

        steps = self._get_test_steps_list()
        new_step = {"values": [TextContent(content=arg).to_soap() for arg in args]}
        steps.append(new_step)
        self._polarion_test_steps["steps"] = steps

        self._polarion._soap.call("TestManagement", "setTestSteps", workitemURI=self.uri, steps=steps)
        self._reload_from_polarion()

    def remove_test_step(self, index: int) -> None:
        """Remove a test step at the given index."""
        if not self._has_test_step_field():
            raise PolarionFieldError("Cannot remove test steps: custom field not available")

        steps = self._get_test_steps_list()
        if index >= len(steps):
            raise ValueError(f"Index {index} out of range (length {len(steps)})")

        steps.pop(index)
        self._polarion._soap.call("TestManagement", "setTestSteps", workitemURI=self.uri, steps=steps)
        self._reload_from_polarion()

    def update_test_step(self, index: int, *args: str) -> None:
        """Update a test step at the given index.

        :param index: Zero-based step index
        :param args: One string per column
        """
        if not self._has_test_step_field():
            raise PolarionFieldError("Cannot update test steps: custom field not available")

        steps = self._get_test_steps_list()
        if index >= len(steps):
            raise ValueError(f"Index {index} out of range (length {len(steps)})")

        keys = self._polarion_test_steps.get("keys")
        num_columns = len(self._extract_enum_ids(keys)) if keys else 0
        if len(args) != num_columns:
            raise PolarionFieldError(f"Test step requires {num_columns} arguments, got {len(args)}")

        steps[index] = {"values": [TextContent(content=arg).to_soap() for arg in args]}
        self._polarion._soap.call("TestManagement", "setTestSteps", workitemURI=self.uri, steps=steps)
        self._reload_from_polarion()

    def _get_test_steps_list(self) -> list:
        """Get the current test steps as a mutable list."""
        steps = self._polarion_test_steps.get("steps") if self._polarion_test_steps else None
        return ensure_list(steps)

    def _has_test_step_field(self) -> bool:
        """Check if testSteps custom field is available."""
        return self.is_custom_field_allowed("testSteps")

    def _get_configured_test_step_attrs(self, attr: str = "name") -> list[str]:
        result = self._polarion._soap.call("TestManagement", "getTestStepsConfiguration", projectId=self._project.id)
        if isinstance(result, list):
            return [col.get(attr, "") if isinstance(col, dict) else str(col) for col in result]
        return []

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
