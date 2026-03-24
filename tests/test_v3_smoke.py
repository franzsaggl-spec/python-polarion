from polarion import PolarionClient


def test_v3_client_exposed():
    client = PolarionClient(url="http://example", username="u", password="p")
    assert client.projects is not None
    assert client.workitems is not None
    assert client.documents is not None
    assert client.plans is not None
    assert client.testruns is not None
    assert client.users is not None
