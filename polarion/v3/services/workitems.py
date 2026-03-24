from __future__ import annotations

from ..types.common import AttachmentMeta, Link, Page
from ..types.workitem import WorkitemCreate, WorkitemDetail, WorkitemSummary, WorkitemUpdate
from .base import ServiceBase


class WorkitemsService(ServiceBase):
    def get(self, project_id: str, workitem_id: str) -> WorkitemDetail:
        raise NotImplementedError

    def get_by_uri(self, uri: str) -> WorkitemDetail:
        raise NotImplementedError

    def create(self, project_id: str, payload: WorkitemCreate) -> WorkitemDetail:
        raise NotImplementedError

    def update(self, project_id: str, workitem_id: str, payload: WorkitemUpdate) -> WorkitemDetail:
        raise NotImplementedError

    def delete(self, project_id: str, workitem_id: str) -> None:
        raise NotImplementedError

    def search(
        self,
        project_id: str,
        query: str | None = None,
        *,
        sort: str = "Created",
        fields: list[str] | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Page[WorkitemSummary]:
        raise NotImplementedError

    def available_actions(self, project_id: str, workitem_id: str) -> list[str]:
        raise NotImplementedError

    def available_statuses(self, project_id: str, workitem_id: str) -> list[str]:
        raise NotImplementedError

    def perform_action(self, project_id: str, workitem_id: str, action: str) -> WorkitemDetail:
        raise NotImplementedError

    def links(self, project_id: str, workitem_id: str) -> list[Link]:
        raise NotImplementedError

    def add_link(self, project_id: str, workitem_id: str, target_workitem_id: str, role: str) -> None:
        raise NotImplementedError

    def remove_link(self, project_id: str, workitem_id: str, target_workitem_id: str, role: str | None = None) -> None:
        raise NotImplementedError

    def add_hyperlink(self, project_id: str, workitem_id: str, url: str, role: str) -> None:
        raise NotImplementedError

    def remove_hyperlink(self, project_id: str, workitem_id: str, url: str) -> None:
        raise NotImplementedError

    def attachments(self, project_id: str, workitem_id: str) -> list[AttachmentMeta]:
        raise NotImplementedError

    def upload_attachment(
        self, project_id: str, workitem_id: str, file_path: str, title: str | None = None
    ) -> AttachmentMeta:
        raise NotImplementedError

    def download_attachment(self, project_id: str, workitem_id: str, attachment_id: str) -> bytes:
        raise NotImplementedError

    def delete_attachment(self, project_id: str, workitem_id: str, attachment_id: str) -> None:
        raise NotImplementedError

    def test_steps(self, project_id: str, workitem_id: str) -> list[dict[str, str]]:
        raise NotImplementedError

    def test_step_columns(self, project_id: str, workitem_id: str) -> list[str]:
        raise NotImplementedError

    def add_test_step(self, project_id: str, workitem_id: str, values: list[str]) -> None:
        raise NotImplementedError

    def update_test_step(self, project_id: str, workitem_id: str, index: int, values: list[str]) -> None:
        raise NotImplementedError

    def remove_test_step(self, project_id: str, workitem_id: str, index: int) -> None:
        raise NotImplementedError
