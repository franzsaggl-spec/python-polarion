"""Test run-related project behavior mixin."""

from __future__ import annotations

from ..factory import create_from_uri
from ..testrun import Testrun


class ProjectTestRunsMixin:
    def get_test_run(self, id: str) -> Testrun:
        """Get a test run by ID.

        :param id: Test run ID
        """
        uri = f"subterra:data-service:objects:/default/{self.id}${{TestRun}}{id}"
        return Testrun(self.polarion, uri=uri)

    def search_test_runs(self, query: str = "", order: str = "Created", limit: int = 100) -> list[Testrun]:
        """Search for test runs.

        :param query: Polarion query
        :param order: Sort field
        :param limit: Maximum results
        """
        results = self.polarion._soap.call(
            "TestManagement", "searchTestRunsLimited", query=self._scoped_query(query), sort=order, limit=limit
        )
        if not isinstance(results, list):
            return []
        return [Testrun(self.polarion, polarion_test_run=tr) for tr in results if tr]

    def create_test_run(self, id: str, title: str, template_id: str) -> Testrun:
        """Create a new test run from a template.

        :param id: New test run ID
        :param title: Test run title
        :param template_id: Template test run ID
        """
        new_uri = self.polarion._soap.call(
            "TestManagement",
            "createTestRunWithTitle",
            projectId=self.id,
            testRunId=id,
            title=title,
            templateId=template_id,
        )
        return create_from_uri(self.polarion, self, new_uri)
