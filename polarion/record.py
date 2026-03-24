"""Polarion Test Record model."""

from __future__ import annotations

import os
from enum import Enum
from typing import TYPE_CHECKING, Any

from .base.polarion_object import BatchSaveMixin, PolarionObject
from .exceptions import PolarionNotFoundError
from .factory import create_from_uri
from .types import TextContent
from .utils import ensure_list

if TYPE_CHECKING:
    from .client import Polarion
    from .testrun import Testrun
    from .user import User


class Record(PolarionObject, BatchSaveMixin):
    """A test record within a test run.

    :param polarion: Polarion client
    :param test_run: Parent test run
    :param polarion_record: Record data dict
    :param index: Index in the test run
    """

    _default_summary_fields = ["testcase_id", "result", "executed"]
    _field_accessors = {
        "testcase_id": lambda self: self.testcase_id,
        "result": lambda self: self.get_result(),
    }

    class ResultType(Enum):
        """Test execution result types.

        No: No result has been recorded yet (value is None).
        """

        No = None
        PASSED = "passed"
        FAILED = "failed"
        BLOCKED = "blocked"
        NOTTESTED = "not_tested"

    # Declared attributes
    result: Any = None
    comment: Any = None
    executed: Any = None
    executedByURI: str | None = None
    duration: str | None = None
    testCaseURI: str | None = None
    testStepResults: Any = None
    attachments: Any = None

    def __init__(
        self,
        polarion: Polarion,
        test_run: Testrun,
        polarion_record: dict[str, Any],
        index: int,
    ) -> None:
        super().__init__(polarion, None, None, None)
        self._test_run = test_run
        self._polarion_record = polarion_record
        self._index = index

        self._build_from_polarion()

    def _build_from_polarion(self) -> None:
        self._populate_from_dict(self, self._polarion_record)

        self._testcase = self._polarion_record.get("testCaseURI", "")
        self._testcase_name = self._testcase.split("}")[-1] if "}" in self._testcase else self._testcase

    def _reload_from_polarion(self) -> None:
        result = self._polarion._soap.call(
            "TestManagement", "getTestCaseRecords", testRunURI=self._test_run.uri, testCaseURI=self._testcase
        )
        if isinstance(result, list) and result:
            self._polarion_record = result[0]
        elif isinstance(result, dict):
            self._polarion_record = result
        self._build_from_polarion()

    def set_test_step_result(
        self,
        step_number: int,
        result: ResultType,
        comment: str | None = None,
    ) -> None:
        """Set the result of a test step.

        :param step_number: Step index
        :param result: Result value
        :param comment: Optional comment
        """
        if self.testStepResults is None:
            test_steps = self._polarion._soap.call("TestManagement", "getTestSteps", workitemURI=self.testCaseURI)
            num_steps = 0
            if isinstance(test_steps, dict):
                steps = test_steps.get("steps", [])
                if isinstance(steps, list):
                    num_steps = len(steps)
            self.testStepResults = [{"result": None, "comment": None} for _ in range(num_steps)]

        self.testStepResults = ensure_list(self.testStepResults)

        if step_number < len(self.testStepResults):
            step_result = self.testStepResults[step_number]
            if isinstance(step_result, dict):
                step_result["result"] = {"id": result.value}
                if comment is not None:
                    step_result["comment"] = TextContent(content=comment).to_soap()
            else:
                self.testStepResults[step_number] = {
                    "result": {"id": result.value},
                    "comment": TextContent(content=comment).to_soap() if comment else None,
                }

    def get_result(self) -> ResultType:
        """Get the test result."""
        if self.result is not None:
            result_id = self.result.get("id") if isinstance(self.result, dict) else self.result
            if result_id:
                return self.ResultType(result_id)
        return self.ResultType.No

    def get_comment(self) -> str | None:
        """Get the comment (may contain HTML)."""
        if self.comment is not None:
            if isinstance(self.comment, dict):
                return self.comment.get("content")
            return str(self.comment)
        return None

    @property
    def testcase_id(self) -> str:
        """The test case ID including prefix."""
        return self._testcase_name

    def get_test_case_name(self) -> str:
        """Get the test case name including prefix."""
        return self._testcase_name

    def set_comment(self, comment: str) -> None:
        """Set the comment for this record."""
        self.comment = TextContent(content=comment).to_soap()

    def set_result(
        self,
        result: ResultType = ResultType.FAILED,
        comment: str | None = None,
    ) -> None:
        """Set the result and save.

        :param result: Test result
        :param comment: Optional comment
        """
        if comment is not None:
            self.set_comment(comment)
        if isinstance(self.result, dict):
            self.result["id"] = result.value
        else:
            self.result = {"id": result.value}

    def get_executing_user(self) -> User | None:
        """Get the user who executed this test."""
        if self.executedByURI is not None:
            return create_from_uri(self._polarion, None, self.executedByURI)
        return None

    def has_attachment(self) -> bool:
        """Check if this record has attachments."""
        return self.attachments is not None

    def get_attachment(self, file_name: str) -> bytes:
        """Get attachment data by file name."""
        if self.attachments is not None:
            for att in ensure_list(self.attachments):
                if isinstance(att, dict) and att.get("fileName") == file_name:
                    url = att.get("url")
                    if url:
                        return self._polarion.download_from_svn(url)
        raise PolarionNotFoundError(f"Could not find attachment {file_name}")

    def save_attachment_as_file(self, file_name: str, file_path: str) -> None:
        """Save an attachment to a file."""
        data = self.get_attachment(file_name)
        with open(file_path, "wb") as f:
            f.write(data)

    def delete_attachment(self, file_name: str) -> None:
        """Delete an attachment."""
        self._polarion._soap.call(
            "TestManagement",
            "deleteAttachmentFromTestRecord",
            testRunURI=self._test_run.uri,
            index=self._index,
            fileName=file_name,
        )
        self._reload_from_polarion()

    def add_attachment(self, file_path: str, title: str) -> None:
        """Upload an attachment."""
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            self._polarion._soap.call(
                "TestManagement",
                "addAttachmentToTestRecord",
                testRunURI=self._test_run.uri,
                index=self._index,
                fileName=file_name,
                title=title,
                content=f.read(),
            )
        self._reload_from_polarion()

    def test_step_has_attachment(self, step_index: int) -> bool:
        """Check if a test step has attachments."""
        results = ensure_list(self.testStepResults)
        if step_index < len(results):
            step = results[step_index]
            if isinstance(step, dict):
                return step.get("attachments") is not None
        return False

    def get_attachment_from_test_step(self, step_index: int, file_name: str) -> bytes:
        """Get attachment data from a test step."""
        results = ensure_list(self.testStepResults)
        if step_index < len(results):
            step = results[step_index]
            if isinstance(step, dict):
                for att in ensure_list(step.get("attachments")):
                    if isinstance(att, dict) and att.get("fileName") == file_name:
                        url = att.get("url")
                        if url:
                            return self._polarion.download_from_svn(url)
        raise PolarionNotFoundError(f"Could not find attachment {file_name}")

    def save_attachment_from_test_step_as_file(self, step_index: int, file_name: str, file_path: str) -> None:
        """Save a test step attachment to a file."""
        data = self.get_attachment_from_test_step(step_index, file_name)
        with open(file_path, "wb") as f:
            f.write(data)

    def delete_attachment_from_test_step(self, step_index: int, file_name: str) -> None:
        """Delete an attachment from a test step."""
        self._polarion._soap.call(
            "TestManagement",
            "deleteAttachmentFromTestStep",
            testRunURI=self._test_run.uri,
            recordIndex=self._index,
            stepIndex=step_index,
            fileName=file_name,
        )
        self._reload_from_polarion()

    def add_attachment_to_test_step(self, step_index: int, file_path: str, title: str) -> None:
        """Upload an attachment to a test step."""
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            self._polarion._soap.call(
                "TestManagement",
                "addAttachmentToTestStep",
                testRunURI=self._test_run.uri,
                recordIndex=self._index,
                stepIndex=step_index,
                fileName=file_name,
                title=title,
                content=f.read(),
            )
        self._reload_from_polarion()

    def save(self) -> None:
        """Save the test record."""
        if self._batch_save:
            return

        _RECORD_FIELDS = (
            "result",
            "comment",
            "executed",
            "executedByURI",
            "duration",
            "testCaseURI",
            "testStepResults",
            "attachments",
        )
        new_item: dict[str, Any] = {}
        for field in _RECORD_FIELDS:
            value = getattr(self, field, None)
            if value is not None:
                new_item[field] = value

        self._polarion._soap.call("TestManagement", "executeTest", testRunURI=self._test_run.uri, record=new_item)
        self._reload_from_polarion()

    def __repr__(self) -> str:
        return f"{self._testcase_name} in {self._test_run.id} ({self.get_result()} on {self.executed})"

    __str__ = __repr__
