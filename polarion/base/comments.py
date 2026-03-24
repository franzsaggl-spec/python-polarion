"""Comments mixin for Polarion objects."""

from __future__ import annotations

from abc import ABC

from polarion.base.polarion_object import PolarionObject
from polarion.exceptions import PolarionApiError, PolarionFieldError


class Comments(PolarionObject, ABC):
    """Mixin providing comment operations on Polarion objects."""

    def add_comment(
        self,
        title: str | None,
        comment: str,
        parent: str | None = None,
        content_type: str = "html",
    ) -> None:
        """Add a comment to this item.

        :param title: Title of the comment (None for replies)
        :param comment: Comment text (may contain HTML)
        :param parent: Parent comment URI for replies. If None, added as root comment.
        :param content_type: "html" or "plain" (expanded to "text/html" or "text/plain")
        :raises PolarionFieldError: If content_type is invalid
        :raises PolarionApiError: If comments are disabled
        """
        if content_type not in ("html", "plain"):
            raise PolarionFieldError("content_type must be either 'html' or 'plain'")

        if parent is None:
            parent = self.uri
        else:
            title = None  # replies cannot have titles

        content = {
            "type": f"text/{content_type}",
            "content": comment,
            "contentLossy": False,
        }

        try:
            self._polarion._soap.call(
                "Tracker",
                "addComment",
                parentURI=parent,
                title=title,
                content=content,
            )
            self._reload_from_polarion()
        except Exception as e:
            raise PolarionApiError(f"Could not add comment: {e}. Adding comments might be disabled.") from e
