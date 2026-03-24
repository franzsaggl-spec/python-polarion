"""Polarion Test Run model."""

from __future__ import annotations

import copy
import os
from typing import TYPE_CHECKING, Any

from .base.comments import Comments
from .base.custom_fields import CustomFields
from .exceptions import PolarionFieldError, PolarionNotFoundError
from .factory import Creator
from .record import Record
from .utils import ensure_list

if TYPE_CHECKING:
    from .client import Polarion
    from .workitem import Workitem


class Testrun(CustomFields, Comments):
    __test__ = False
    """A Polarion test run.

    :param polarion: Polarion client
    :param uri: Test run URI
    :param polarion_test_run: Pre-fetched test run data
    """

    _default_summary_fields = ["id", "title", "created", "isTemplate"]

    # Declared attributes
    id: str | None = None
    title: str | None = None
    created: Any = None
    isTemplate: bool | None = None
    attachments: Any = None
    status: Any = None

    def __init__(
        self,
        polarion: Polarion,
        uri: str | None = None,
        polarion_test_run: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(polarion, None, None, uri)
        self._polarion_data: dict[str, Any] = {}
        self._original_data: dict[str, Any] = {}

        if uri is not None:
            try:
                self._polarion_data = self._polarion._soap.call("TestManagement", "getTestRunByUri", uri=uri)
            except Exception as e:
                raise PolarionNotFoundError(f"Cannot find test run {uri}") from e

        elif polarion_test_run is not None:
            self._polarion_data = polarion_test_run
        else:
            raise PolarionFieldError("Provide either a uri or polarion_test_run data")

        self._original_data = copy.deepcopy(self._polarion_data)
        self._build_from_polarion()

    def is_custom_field_allowed(self, key: str) -> bool:
        return True

    def _build_from_polarion(self) -> None:
        if not isinstance(self._polarion_data, dict) or self._polarion_data.get("unresolvable"):
            raise PolarionNotFoundError("Testrun not retrieved from Polarion")

        # Remap 'records' to avoid conflict with our records list
        data = dict(self._polarion_data)
        raw_records = data.pop("records", None)
        self._populate_from_dict(self, data)
        self._uri = data.get("uri", self._uri)

        self.records: list[Record] = []
        self._record_dict: dict[str, Record] = {}
        if raw_records is not None:
            for index, r in enumerate(ensure_list(raw_records)):
                if isinstance(r, dict):
                    new_record = Record(self._polarion, self, r, index)
                    self.records.append(new_record)
                    if new_record.testcase_id not in self._record_dict:
                        self._record_dict[new_record.testcase_id] = new_record

    def _reload_from_polarion(self) -> None:
        self._polarion_data = self._polarion._soap.call("TestManagement", "getTestRunByUri", uri=self.uri)
        self._build_from_polarion()
        self._original_data = copy.deepcopy(self._polarion_data)

    def has_test_case(self, id: str) -> bool:
        """Check if a test case is in this run's records."""
        return id in self._record_dict

    def get_test_case(self, id: str) -> Record | None:
        """Get a test record by test case ID."""
        return self._record_dict.get(id)

    def has_attachment(self) -> bool:
        """Check if the test run has attachments."""
        return self.attachments is not None

    def get_attachment(self, file_name: str) -> bytes:
        """Get attachment data by file name."""
        at = self._polarion._soap.call(
            "TestManagement", "getTestRunAttachment", testRunURI=self.uri, fileName=file_name
        )
        if at is not None and isinstance(at, dict):
            url = at.get("url")
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
        self._polarion._soap.call("TestManagement", "deleteTestRunAttachment", testRunURI=self.uri, fileName=file_name)
        self._reload_from_polarion()

    def add_attachment(self, file_path: str, title: str) -> None:
        """Upload an attachment."""
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            self._polarion._soap.call(
                "TestManagement",
                "addAttachmentToTestRun",
                testRunURI=self.uri,
                fileName=file_name,
                title=title,
                content=f.read(),
            )
        self._reload_from_polarion()

    def update_attachment(self, file_path: str, title: str) -> None:
        """Update an existing attachment."""
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            self._polarion._soap.call(
                "TestManagement",
                "updateTestRunAttachment",
                testRunURI=self.uri,
                fileName=file_name,
                title=title,
                content=f.read(),
            )
        self._reload_from_polarion()

    def add_test_case(self, workitem: Workitem) -> None:
        """Add a test case work item to this run."""
        self._polarion._soap.call(
            "TestManagement", "addTestRecordToTestRun", testRunURI=self.uri, record={"testCaseURI": workitem.uri}
        )
        self._reload_from_polarion()

    def save(self) -> None:
        """Save changes to Polarion."""
        changed = self._collect_changes(self, self._polarion_data, self._original_data, skip={"records"})
        if changed:
            changed["uri"] = self.uri
            self._polarion._soap.call("TestManagement", "updateTestRun", content=changed)
            self._reload_from_polarion()

    def __repr__(self) -> str:
        return f"Testrun {self.id} ({self._truncate(self.title)}) created {self.created}"

    __str__ = __repr__


class TestrunCreator(Creator):
    def create_from_uri(self, polarion: Polarion, project: Any, uri: str) -> Testrun:
        return Testrun(polarion, uri)
