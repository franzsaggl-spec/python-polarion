"""Attachment helpers for Workitem."""

from __future__ import annotations

import os


class WorkitemAttachmentMixin:
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
