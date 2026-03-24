from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_projects_get_live(live_client, project_id):
    project = live_client.projects.get(project_id)
    assert project.id
    assert project.name


def test_projects_users_live(live_client, project_id):
    page = live_client.projects.users(project_id, offset=0, limit=10)
    assert page.offset == 0
    assert page.limit == 10
    assert isinstance(page.items, list)


def test_workitems_search_live(live_client, project_id):
    page = live_client.workitems.search(project_id, query="", limit=5)
    assert page.limit == 5
    assert isinstance(page.items, list)


def test_documents_spaces_live(live_client, project_id):
    spaces = live_client.documents.list_spaces(project_id)
    assert isinstance(spaces, list)


def test_testruns_search_live(live_client, project_id):
    page = live_client.testruns.search(project_id, query="", limit=5)
    assert page.limit == 5
    assert isinstance(page.items, list)
