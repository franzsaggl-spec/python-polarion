"""Test-step helpers for Workitem."""

from __future__ import annotations

import logging

from ..exceptions import PolarionFieldError
from ..types import TextContent
from ..utils import ensure_list

logger = logging.getLogger(__name__)


class WorkitemTestStepMixin:
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
