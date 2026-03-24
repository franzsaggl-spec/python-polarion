"""Workflow/status/action helpers for Workitem."""

from __future__ import annotations

import logging
from typing import Any

from ..exceptions import PolarionApiError, PolarionFieldError

logger = logging.getLogger(__name__)


class WorkitemWorkflowMixin:
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
