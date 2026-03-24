"""Polarion client — main entry point for the library.

Usage:
    from polarion import Polarion

    with Polarion("https://polarion.example.com/polarion", "user", password="pw") as client:
        project = client.get_project("MyProject")
        wi = project.get_workitem("REQ-123")
"""

from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urlparse

import requests

from .exceptions import (
    PolarionApiError,
    PolarionAuthError,
)
from .project import Project
from .soap.client import SoapClient

logger = logging.getLogger(__name__)

_SESSION_CHECK_INTERVAL = 300  # seconds


class Polarion:
    """Polarion client for communicating with a Polarion ALM server.

    :param polarion_url: Base URL (e.g. "https://example.com/polarion")
    :param user: Username
    :param password: Password (required if token not provided)
    :param token: Personal access token (alternative to password)
    :param static_service_list: If True, use a static service list instead of fetching
    :param verify_certificate: SSL verification (bool or CA bundle path)
    :param svn_repo_url: Custom SVN repo URL if different from default
    :param proxy: Proxy address ("ip:port")
    """

    def __init__(
        self,
        polarion_url: str,
        user: str,
        password: str | None = None,
        token: str | None = None,
        static_service_list: bool = False,
        verify_certificate: bool | str = True,
        svn_repo_url: str | None = None,
        proxy: str | None = None,
    ) -> None:
        self.user = user
        self._password = password
        self._token = token
        self.url = polarion_url.rstrip("/")
        self.verify_certificate = verify_certificate
        self.svn_repo_url = svn_repo_url

        self._soap = SoapClient(
            base_url=self.url,
            verify_certificate=verify_certificate,
            proxy=proxy,
        )

        self._soap.discover_services(static=static_service_list)
        self._login()
        self._last_session_check = time.time()

    def _login(self) -> None:
        """Authenticate with the server."""
        if self._token is not None:
            self._soap.login_with_token(self.user, self._token)
        elif self._password is not None:
            self._soap.login(self.user, self._password)
        else:
            raise PolarionAuthError("Either password or token must be provided")

    def _check_session(self) -> None:
        """Periodically verify the session is still valid, re-login if needed."""
        if time.time() - self._last_session_check > _SESSION_CHECK_INTERVAL:
            try:
                self._soap.call("Project", "getUser", userId=self.user)
                self._last_session_check = time.time()
            except Exception:
                self._login()
                self._last_session_check = time.time()

    def get_project(self, project_id: str) -> Project:
        """Get a Polarion project.

        :param project_id: The project ID
        :return: Project instance
        """
        return Project(self, project_id)

    def query_workitems(self, query: str, sort: str) -> list[Any]:
        """Query work items globally across all projects.

        Use with caution — returns work items from all projects.
        Uses Polarion query language ('Advanced Work Item querying').

        :param query: Polarion query string
        :param sort: Sort field
        :return: List of Workitem objects
        """
        from .workitem import Workitem

        self._check_session()
        results = self._soap.call(
            "Tracker",
            "queryWorkItems",
            query=query,
            sort=sort,
            fields=["project.id"],
        )

        workitems = []
        if results is None:
            return workitems

        if not isinstance(results, list):
            results = [results]

        for result in results:
            if isinstance(result, dict):
                project_data = result.get("project", {})
                project_id = project_data.get("id", "") if isinstance(project_data, dict) else ""
                project = self.get_project(project_id)
                uri = result.get("uri", "")
                workitems.append(Workitem(self, project, uri=uri))

        return workitems

    def download_from_svn(self, url: str) -> bytes:
        """Download content from the Polarion SVN repository.

        :param url: SVN URL
        :return: File content as bytes
        :raises PolarionApiError: If download fails
        """
        download_url = url
        if self.svn_repo_url is not None:
            orig_url = urlparse(url)
            orig_url_path_without_repo = "/".join(orig_url.path.split("/")[2:])
            new_root_url = urlparse(self.svn_repo_url)
            download_url = (
                f"{new_root_url.scheme}://{new_root_url.netloc}"
                f"/{new_root_url.path.strip('/')}/{orig_url_path_without_repo}"
            )

        resp = requests.get(
            download_url,
            auth=(self.user, self._password or ""),
            verify=self.verify_certificate,
        )
        if resp.ok:
            return resp.content
        raise PolarionApiError(f"Could not download from {url}. Got {resp.status_code}: {resp.reason}")

    def has_service(self, name: str) -> bool:
        """Check if a WSDL service is available."""
        return self._soap.has_service(name)

    def close(self) -> None:
        """End the session and close connections."""
        self._soap.logout()
        self._soap.close()

    def __enter__(self) -> Polarion:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Polarion client for {self.url} with user {self.user}"

    __str__ = __repr__
