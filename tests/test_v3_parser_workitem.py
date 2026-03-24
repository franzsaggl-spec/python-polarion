from datetime import datetime

import pytest

from polarion.v3.errors import ParsingError
from polarion.v3.parser.workitem import parse_workitem_detail


def _raw(created=None, updated=None):
    return {
        "id": "WI-1",
        "_uri": "uri:WI-1",
        "title": "Title",
        "type": {"id": "task"},
        "status": {"id": "open"},
        "priority": {"id": "high"},
        "created": created,
        "updated": updated,
    }


def test_parse_workitem_detail_parses_datetimes():
    wi = parse_workitem_detail(_raw("2026-03-24T12:00:00Z", "2026-03-24T13:00:00+00:00"))
    assert isinstance(wi.created_at, datetime)
    assert isinstance(wi.updated_at, datetime)


def test_parse_workitem_detail_invalid_datetime_raises():
    with pytest.raises(ParsingError):
        parse_workitem_detail(_raw("not-a-date", None))
