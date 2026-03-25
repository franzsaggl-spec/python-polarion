from __future__ import annotations

import os

import pytest


pytestmark = pytest.mark.integration


def test_v3_happy_path_flow(live_client, project_id):
    # 1) project
    project = live_client.projects.get(project_id)
    assert project.id

    # 2) workitems
    workitems = live_client.workitems.search(project_id, query="", limit=5)
    assert isinstance(workitems.items, list)

    # 3) plans
    plans = live_client.plans.search(project_id, query="", limit=5)
    assert isinstance(plans.items, list)

    # 4) test runs
    runs = live_client.testruns.search(project_id, query="", limit=5)
    assert isinstance(runs.items, list)

    # 5) documents (if at least one space exists)
    spaces = live_client.documents.list_spaces(project_id)
    if spaces:
        docs = live_client.documents.list_in_space(project_id, spaces[0], limit=5)
        assert isinstance(docs.items, list)


@pytest.mark.integration
def test_optional_deep_get_flow(live_client, project_id):
    workitem_id = os.getenv("POLARION_WORKITEM_ID")
    plan_id = os.getenv("POLARION_PLAN_ID")
    testrun_id = os.getenv("POLARION_TESTRUN_ID")
    document_uri = os.getenv("POLARION_DOCUMENT_URI")

    if workitem_id:
        wi = live_client.workitems.get(project_id, workitem_id)
        assert wi.id

    if plan_id:
        pl = live_client.plans.get(project_id, plan_id)
        assert pl.id

    if testrun_id:
        tr = live_client.testruns.get(project_id, testrun_id)
        assert tr.id

    if document_uri:
        doc = live_client.documents.get(project_id, uri=document_uri)
        assert doc.uri
