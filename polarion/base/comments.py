from __future__ import annotations

import logging
from abc import ABC
from typing import Optional

from polarion.base.polarion_object import PolarionObject
from polarion.exceptions import PolarionFieldError, PolarionApiError

logger = logging.getLogger(__name__)


class Comments(PolarionObject, ABC):

    def addComment(self, title: Optional[str], comment: str, parent: Optional[str] = None, type: str = 'html') -> None:
        """
        Adds a comment to the workitem.

        Throws an exception if the function is disabled in Polarion.

        :param title: Title of the comment (will be None for a reply)
        :param comment: The comment, may contain html
        :param parent: A parent comment, if none provided it's a root comment.
        """
        service = self._polarion.getService('Tracker')
        if type not in ['html', 'plain']:
            raise PolarionFieldError('Type must be either html or plain.')
        if hasattr(service, 'addComment'):
            if parent is None:
                parent = self.uri
            else:
                # force title to be empty, not allowed for reply comments
                title = None
            content = {
                'type': f'text/{type}',
                'content': comment,
                'contentLossy': False
            }
            service.addComment(parent, title, content)
            self._reloadFromPolarion()
        else:
            raise PolarionApiError("addComment binding not found in Tracker Service. Adding comments might be disabled.")
