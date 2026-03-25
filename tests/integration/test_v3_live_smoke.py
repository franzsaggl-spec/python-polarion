from __future__ import annotations

import os

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


def test_documents_list_in_space_live(live_client, project_id):
    spaces = live_client.documents.list_spaces(project_id)
    if not spaces:
        pytest.skip("no document spaces available")
    page = live_client.documents.list_in_space(project_id, spaces[0], limit=5)
    assert page.limit == 5
    assert isinstance(page.items, list)


def test_plans_search_live(live_client, project_id):
    page = live_client.plans.search(project_id, query="", limit=5)
    assert page.limit == 5
    assert isinstance(page.items, list)


def test_optional_get_workitem_by_env_id(live_client, project_id):
    workitem_id = os.getenv("POLARION_WORKITEM_ID")
    if not workitem_id:
        pytest.skip("POLARION_WORKITEM_ID not set")
    wi = live_client.workitems.get(project_id, workitem_id)
    assert wi.id


def test_optional_get_document_by_env_uri(live_client, project_id):
    document_uri = os.getenv("POLARION_DOCUMENT_URI")
    if not document_uri:
        pytest.skip("POLARION_DOCUMENT_URI not set")
    doc = live_client.documents.get(project_id, uri=document_uri)
    assert doc.uri


def test_optional_get_plan_by_env_id(live_client, project_id):
    plan_id = os.getenv("POLARION_PLAN_ID")
    if not plan_id:
        pytest.skip("POLARION_PLAN_ID not set")
    plan = live_client.plans.get(project_id, plan_id)
    assert plan.id


def test_optional_get_testrun_by_env_id(live_client, project_id):
    testrun_id = os.getenv("POLARION_TESTRUN_ID")
    if not testrun_id:
        pytest.skip("POLARION_TESTRUN_ID not set")
    tr = live_client.testruns.get(project_id, testrun_id)
    assert tr.id
