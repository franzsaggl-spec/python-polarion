from __future__ import annotations

from dataclasses import dataclass

from .services.documents import DocumentsService
from .services.plans import PlansService
from .services.projects import ProjectsService
from .services.testruns import TestRunsService
from .services.users import UsersService
from .services.workitems import WorkitemsService
from .transport.soap import SoapTransport


@dataclass
class PolarionClient:
    url: str
    username: str
    password: str | None = None
    token: str | None = None
    verify_ssl: bool = True
    timeout: float = 30.0
    strict: bool = True

    def __post_init__(self) -> None:
        self._transport = SoapTransport(
            url=self.url,
            username=self.username,
            password=self.password,
            token=self.token,
            verify_ssl=self.verify_ssl,
            timeout=self.timeout,
        )
        self.projects = ProjectsService(self._transport)
        self.workitems = WorkitemsService(self._transport)
        self.documents = DocumentsService(self._transport)
        self.plans = PlansService(self._transport)
        self.testruns = TestRunsService(self._transport)
        self.users = UsersService(self._transport)

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> "PolarionClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
