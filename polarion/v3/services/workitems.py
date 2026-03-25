from __future__ import annotations

from ..parser.workitem import parse_workitem_detail, parse_workitem_summary_list
from ..types.common import AttachmentMeta, Link, Page
from ..types.workitem import WorkitemCreate, WorkitemDetail, WorkitemSummary, WorkitemUpdate
from .base import ServiceBase


class WorkitemsService(ServiceBase):
    def get(self, project_id: str, workitem_id: str) -> WorkitemDetail:
        raw = self.transport.call("Tracker", "getWorkItemById", projectId=project_id, id=workitem_id)
        wi = parse_workitem_detail(raw)
        self.require_identifier(wi.id, context=f"workitem {workitem_id}")
        return wi

    def get_by_uri(self, uri: str) -> WorkitemDetail:
        raw = self.transport.call("Tracker", "getWorkItemByUri", uri=uri)
        return parse_workitem_detail(raw)

    def create(self, project_id: str, payload: WorkitemCreate) -> WorkitemDetail:
        raw = self.transport.call(
            "Tracker",
            "createWorkItem",
            projectId=project_id,
            type=payload.type_id,
            title=payload.title,
            description=payload.description_html,
            **payload.fields,
        )
        if isinstance(raw, dict):
            return parse_workitem_detail(raw)
        return self.get(project_id, str(raw))

    def update(self, project_id: str, workitem_id: str, payload: WorkitemUpdate) -> WorkitemDetail:
        fields: dict[str, object] = {}
        if payload.title is not None:
            fields["title"] = payload.title
        if payload.description_html is not None:
            fields["description"] = payload.description_html
        if payload.status_id is not None:
            fields["status"] = payload.status_id
        if payload.resolution_id is not None:
            fields["resolution"] = payload.resolution_id
        if payload.severity_id is not None:
            fields["severity"] = payload.severity_id
        if payload.priority_id is not None:
            fields["priority"] = payload.priority_id
        if payload.assignee_ids is not None:
            fields["assignee"] = payload.assignee_ids
        fields.update(payload.fields)

        self.transport.call("Tracker", "updateWorkItem", projectId=project_id, id=workitem_id, **fields)
        return self.get(project_id, workitem_id)

    def delete(self, project_id: str, workitem_id: str) -> None:
        self.transport.call("Tracker", "deleteWorkItem", projectId=project_id, id=workitem_id)

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
        scoped = f"project.id:{project_id}"
        if query:
            scoped = f"{scoped} AND ({query})"
        raw = self.transport.call(
            "Tracker",
            "queryWorkItems",
            query=scoped,
            sort=sort,
            fields=fields or ["id", "title", "type", "status", "priority"],
        )
        items = parse_workitem_summary_list(raw)
        return self.paginate(items, offset=offset, limit=limit)

    def available_actions(self, project_id: str, workitem_id: str) -> list[str]:
        raw = self.transport.call("Tracker", "getAvailableActions", projectId=project_id, id=workitem_id)
        if isinstance(raw, list):
            return [str(a.get("id") if isinstance(a, dict) else a) for a in raw]
        return []

    def available_statuses(self, project_id: str, workitem_id: str) -> list[str]:
        raw = self.transport.call("Tracker", "getAllowedStatuses", projectId=project_id, id=workitem_id)
        if isinstance(raw, list):
            return [str(s.get("id") if isinstance(s, dict) else s) for s in raw]
        return []

    def perform_action(self, project_id: str, workitem_id: str, action: str) -> WorkitemDetail:
        self.transport.call("Tracker", "performAction", projectId=project_id, id=workitem_id, action=action)
        return self.get(project_id, workitem_id)

    def links(self, project_id: str, workitem_id: str) -> list[Link]:
        return self.get(project_id, workitem_id).links

    def add_link(self, project_id: str, workitem_id: str, target_workitem_id: str, role: str) -> None:
        self.transport.call(
            "Tracker",
            "addLinkedItem",
            projectId=project_id,
            id=workitem_id,
            targetId=target_workitem_id,
            role=role,
        )

    def remove_link(self, project_id: str, workitem_id: str, target_workitem_id: str, role: str | None = None) -> None:
        self.transport.call(
            "Tracker",
            "removeLinkedItem",
            projectId=project_id,
            id=workitem_id,
            targetId=target_workitem_id,
            role=role,
        )

    def add_hyperlink(self, project_id: str, workitem_id: str, url: str, role: str) -> None:
        self.transport.call("Tracker", "addHyperlink", projectId=project_id, id=workitem_id, url=url, role=role)

    def remove_hyperlink(self, project_id: str, workitem_id: str, url: str) -> None:
        self.transport.call("Tracker", "removeHyperlink", projectId=project_id, id=workitem_id, url=url)

    def attachments(self, project_id: str, workitem_id: str) -> list[AttachmentMeta]:
        return self.get(project_id, workitem_id).attachments

    def upload_attachment(
        self, project_id: str, workitem_id: str, file_path: str, title: str | None = None
    ) -> AttachmentMeta:
        raw = self.transport.call(
            "Tracker",
            "addAttachment",
            projectId=project_id,
            id=workitem_id,
            path=file_path,
            title=title,
        )
        if isinstance(raw, dict):
            return AttachmentMeta(
                id=str(raw.get("id", "")),
                file_name=str(raw.get("fileName", "")),
                title=raw.get("title"),
                url=raw.get("url") or raw.get("_uri"),
            )
        return AttachmentMeta(id="", file_name=file_path, title=title, url=None)

    def download_attachment(self, project_id: str, workitem_id: str, attachment_id: str) -> bytes:
        raw = self.transport.call(
            "Tracker", "getAttachment", projectId=project_id, id=workitem_id, attachmentId=attachment_id
        )
        if isinstance(raw, bytes):
            return raw
        if isinstance(raw, str):
            return raw.encode()
        return b""

    def delete_attachment(self, project_id: str, workitem_id: str, attachment_id: str) -> None:
        self.transport.call(
            "Tracker", "deleteAttachment", projectId=project_id, id=workitem_id, attachmentId=attachment_id
        )

    def test_steps(self, project_id: str, workitem_id: str) -> list[dict[str, str]]:
        raw = self.transport.call("TestManagement", "getTestSteps", projectId=project_id, id=workitem_id)
        return raw if isinstance(raw, list) else []

    def test_step_columns(self, project_id: str, workitem_id: str) -> list[str]:
        raw = self.transport.call("TestManagement", "getTestStepKeys", projectId=project_id, id=workitem_id)
        return [str(k) for k in raw] if isinstance(raw, list) else []

    def add_test_step(self, project_id: str, workitem_id: str, values: list[str]) -> None:
        self.transport.call("TestManagement", "addTestStep", projectId=project_id, id=workitem_id, values=values)

    def update_test_step(self, project_id: str, workitem_id: str, index: int, values: list[str]) -> None:
        self.transport.call(
            "TestManagement", "updateTestStep", projectId=project_id, id=workitem_id, index=index, values=values
        )

    def remove_test_step(self, project_id: str, workitem_id: str, index: int) -> None:
        self.transport.call("TestManagement", "removeTestStep", projectId=project_id, id=workitem_id, index=index)
