from __future__ import annotations

from ..types.common import AttachmentMeta, Page
from ..types.testrun import TestRecord, TestRun, TestRunCreate
from .base import ServiceBase


class TestRunsService(ServiceBase):
    def get(self, project_id: str, test_run_id: str) -> TestRun:
        raise NotImplementedError

    def get_by_uri(self, uri: str) -> TestRun:
        raise NotImplementedError

    def search(
        self,
        project_id: str,
        query: str | None = None,
        *,
        sort: str = "Created",
        offset: int = 0,
        limit: int = 100,
    ) -> Page[TestRun]:
        raise NotImplementedError

    def create(self, project_id: str, payload: TestRunCreate) -> TestRun:
        raise NotImplementedError

    def update(self, test_run: TestRun) -> TestRun:
        raise NotImplementedError

    def records(self, test_run_uri: str, *, offset: int = 0, limit: int = 500) -> Page[TestRecord]:
        raise NotImplementedError

    def add_test_case(self, test_run_uri: str, workitem_uri: str) -> None:
        raise NotImplementedError

    def attachments(self, test_run_uri: str) -> list[AttachmentMeta]:
        raise NotImplementedError

    def upload_attachment(self, test_run_uri: str, file_path: str, title: str | None = None) -> AttachmentMeta:
        raise NotImplementedError

    def download_attachment(self, test_run_uri: str, file_name: str) -> bytes:
        raise NotImplementedError

    def delete_attachment(self, test_run_uri: str, file_name: str) -> None:
        raise NotImplementedError
