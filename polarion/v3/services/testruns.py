from __future__ import annotations

from ..parser.common import maybe_list
from ..parser.testrun import parse_testrun, parse_testrun_list
from ..types.common import AttachmentMeta, Page
from ..types.testrun import TestRecord, TestRun, TestRunCreate
from .base import ServiceBase


class TestRunsService(ServiceBase):
    def get(self, project_id: str, test_run_id: str) -> TestRun:
        raw = self.transport.call("TestManagement", "getTestRunById", projectId=project_id, id=test_run_id)
        tr = parse_testrun(raw)
        self.require_identifier(tr.id, context=f"test run {test_run_id}")
        return tr

    def get_by_uri(self, uri: str) -> TestRun:
        raw = self.transport.call("TestManagement", "getTestRunByUri", uri=uri)
        return parse_testrun(raw)

    def search(
        self,
        project_id: str,
        query: str | None = None,
        *,
        sort: str = "Created",
        offset: int = 0,
        limit: int = 100,
    ) -> Page[TestRun]:
        raw = self.transport.call(
            "TestManagement", "searchTestRuns", projectId=project_id, query=query or "", sort=sort
        )
        items = parse_testrun_list(raw)
        sliced = items[offset : offset + limit]
        return Page(
            items=sliced, total=len(items), offset=offset, limit=limit, has_more=offset + len(sliced) < len(items)
        )

    def create(self, project_id: str, payload: TestRunCreate) -> TestRun:
        raw = self.transport.call(
            "TestManagement",
            "createTestRun",
            projectId=project_id,
            id=payload.id,
            title=payload.title,
            templateId=payload.template_id,
        )
        return parse_testrun(raw)

    def update(self, test_run: TestRun) -> TestRun:
        raw = self.transport.call("TestManagement", "updateTestRun", uri=test_run.uri, title=test_run.title)
        return parse_testrun(raw)

    def records(self, test_run_uri: str, *, offset: int = 0, limit: int = 500) -> Page[TestRecord]:
        raw = self.transport.call("TestManagement", "getTestRunRecords", uri=test_run_uri)
        items = []
        for r in maybe_list(raw):
            if isinstance(r, dict):
                items.append(
                    TestRecord(
                        test_case_id=str(r.get("testCaseId") or ""),
                        result=r.get("result"),
                        duration_ms=r.get("durationMs") if isinstance(r.get("durationMs"), int) else None,
                        comment=r.get("comment"),
                    )
                )
        sliced = items[offset : offset + limit]
        return Page(
            items=sliced, total=len(items), offset=offset, limit=limit, has_more=offset + len(sliced) < len(items)
        )

    def add_test_case(self, test_run_uri: str, workitem_uri: str) -> None:
        self.transport.call(
            "TestManagement", "addTestRecordByObject", testRunUri=test_run_uri, testCaseUri=workitem_uri
        )

    def attachments(self, test_run_uri: str) -> list[AttachmentMeta]:
        raw = self.transport.call("TestManagement", "getTestRunAttachments", uri=test_run_uri)
        items: list[AttachmentMeta] = []
        for a in maybe_list(raw):
            if isinstance(a, dict):
                items.append(
                    AttachmentMeta(
                        id=str(a.get("id", "")),
                        file_name=str(a.get("fileName", "")),
                        title=a.get("title"),
                        url=a.get("_uri") or a.get("url"),
                    )
                )
        return items

    def upload_attachment(self, test_run_uri: str, file_path: str, title: str | None = None) -> AttachmentMeta:
        raw = self.transport.call(
            "TestManagement", "addAttachmentToTestRun", uri=test_run_uri, path=file_path, title=title
        )
        if isinstance(raw, dict):
            return AttachmentMeta(
                id=str(raw.get("id", "")),
                file_name=str(raw.get("fileName", "")),
                title=raw.get("title"),
                url=raw.get("_uri") or raw.get("url"),
            )
        return AttachmentMeta(id="", file_name=file_path, title=title, url=None)

    def download_attachment(self, test_run_uri: str, file_name: str) -> bytes:
        raw = self.transport.call("TestManagement", "getTestRunAttachment", uri=test_run_uri, fileName=file_name)
        if isinstance(raw, bytes):
            return raw
        if isinstance(raw, str):
            return raw.encode()
        return b""

    def delete_attachment(self, test_run_uri: str, file_name: str) -> None:
        self.transport.call("TestManagement", "deleteAttachmentFromTestRun", uri=test_run_uri, fileName=file_name)
