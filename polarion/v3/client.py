from __future__ import annotations

from dataclasses import dataclass

from .errors import AuthError, TransportError
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

    def healthcheck(self) -> dict[str, object]:
        """Lightweight runtime health check for auth + core services."""
        checks: dict[str, bool] = {}
        error: str | None = None
        try:
            # Session probe
            self._transport.call_with_fallback("Session", ["hasSubject", "getMyUserName"])
            checks["session"] = True
        except (AuthError, TransportError) as e:
            checks["session"] = False
            error = str(e)

        # Service-level method existence checks
        checks["project.getProject"] = self._transport.supports_method("Project", "getProject")
        checks["tracker.queryWorkItems"] = self._transport.supports_method("Tracker", "queryWorkItems")
        checks["test.searchTestRuns"] = self._transport.supports_method("TestManagement", "searchTestRuns")

        return {
            "ok": bool(checks.get("session")) and all(v for k, v in checks.items() if k != "session"),
            "checks": checks,
            "error": error,
        }

    def capabilities(self) -> dict[str, object]:
        """Describe server method capability hints used by v3 services."""
        return {
            "services": {
                "Project": {
                    "getProject": self._transport.supports_method("Project", "getProject"),
                    "getProjects": self._transport.supports_method("Project", "getProjects"),
                    "getProjectUsers": self._transport.supports_method("Project", "getProjectUsers"),
                },
                "Tracker": {
                    "queryWorkItems": self._transport.supports_method("Tracker", "queryWorkItems"),
                    "getWorkItemById": self._transport.supports_method("Tracker", "getWorkItemById"),
                    "getModuleByUri": self._transport.supports_method("Tracker", "getModuleByUri"),
                },
                "Planning": {
                    "getPlanById": self._transport.supports_method("Planning", "getPlanById"),
                    "searchPlans": self._transport.supports_method("Planning", "searchPlans"),
                },
                "TestManagement": {
                    "getTestRunById": self._transport.supports_method("TestManagement", "getTestRunById"),
                    "searchTestRuns": self._transport.supports_method("TestManagement", "searchTestRuns"),
                },
            }
        }

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> "PolarionClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
