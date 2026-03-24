"""User-related project behavior mixin."""

from __future__ import annotations

import logging

from ..exceptions import PolarionApiError, PolarionFieldError, PolarionNotFoundError
from ..user import User
from ..utils import ensure_dict, ensure_list

logger = logging.getLogger(__name__)


class ProjectUsersMixin:
    def get_users(self) -> list[User]:
        """Get all users in this project."""
        users: list[User] = []
        project_users = ensure_list(self.polarion._soap.call("Project", "getProjectUsers", projectId=self.id))
        for user_data in project_users:
            try:
                users.append(User(self.polarion, user_data))
            except (PolarionApiError, PolarionNotFoundError, PolarionFieldError) as e:
                name = ensure_dict(user_data).get("name", "unknown")
                logger.warning("Could not retrieve %s: %s", name, e)
        return users

    def find_user(self, name: str) -> User | None:
        """Find a user by ID or name.

        :param name: User ID or display name (case-insensitive)
        """
        for user in self.get_users():
            if user.id.lower() == name.lower() or user.name.lower() == name.lower():
                return user
        return None
