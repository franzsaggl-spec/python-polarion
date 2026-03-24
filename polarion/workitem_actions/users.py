"""User/assignee/approver helpers for Workitem."""

from __future__ import annotations

import logging

from ..exceptions import PolarionApiError, PolarionFieldError, PolarionNotFoundError
from ..user import User
from ..utils import ensure_dict, ensure_list

logger = logging.getLogger(__name__)


class WorkitemUserMixin:
    def get_author(self) -> User | None:
        """Get the author of this work item."""
        if self.author is not None:
            return User(self._polarion, self.author if isinstance(self.author, dict) else {"id": self.author})
        return None

    def get_approver_users(self) -> list[User]:
        """Get the list of approver users."""
        approval_list = ensure_list(self.approvals)
        users = []
        for a in approval_list:
            a_data = ensure_dict(a)
            if a_data:
                user_data = ensure_dict(a_data.get("user")) or {"id": a_data.get("user")}
                try:
                    users.append(User(self._polarion, user_data))
                except (PolarionApiError, PolarionNotFoundError, PolarionFieldError) as e:
                    logger.warning("Skipping unresolvable approver user %s: %s", user_data, e)
        return users

    def add_approvee(self, user: User, remove_others: bool = False) -> None:
        """Add a user as an approvee.

        :param user: User to add
        :param remove_others: If True, remove all other approvees first
        """
        if remove_others:
            for current_user in self.get_approver_users():
                self._polarion._soap.call("Tracker", "removeApprovee", workitemURI=self.uri, userId=current_user.id)

        self._polarion._soap.call("Tracker", "addApprovee", workitemURI=self.uri, userId=user.id)
        self._reload_from_polarion()

    def remove_approvee(self, user: User) -> None:
        """Remove a user from approvees."""
        self._polarion._soap.call("Tracker", "removeApprovee", workitemURI=self.uri, userId=user.id)
        self._reload_from_polarion()

    def get_assigned_users(self) -> list[User]:
        """Get the list of assigned users."""
        user_list = ensure_list(self.assignee)
        users = []
        for u in user_list:
            try:
                users.append(User(self._polarion, u if isinstance(u, dict) else {"id": u}))
            except (PolarionApiError, PolarionNotFoundError, PolarionFieldError) as e:
                logger.warning("Skipping unresolvable assigned user %s: %s", u, e)
        return users

    def add_assignee(self, user: User, remove_others: bool = False) -> None:
        """Add a user as an assignee.

        :param user: User to add
        :param remove_others: If True, remove all other assignees first
        """
        if remove_others:
            for current_user in self.get_assigned_users():
                self._polarion._soap.call("Tracker", "removeAssignee", workitemURI=self.uri, userId=current_user.id)

        self._polarion._soap.call("Tracker", "addAssignee", workitemURI=self.uri, userId=user.id)
        self._reload_from_polarion()

    def remove_assignee(self, user: User) -> None:
        """Remove a user from assignees."""
        self._polarion._soap.call("Tracker", "removeAssignee", workitemURI=self.uri, userId=user.id)
        self._reload_from_polarion()
