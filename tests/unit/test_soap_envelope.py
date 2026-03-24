"""Tests for polarion.soap.envelope — SOAP envelope construction."""

from __future__ import annotations

import base64
from datetime import date, datetime, timezone

from lxml import etree

from polarion.soap.envelope import NIL, NS_SOAP, NS_XSI, _add_param, build_envelope


def _parse_envelope(data: bytes) -> etree._Element:
    """Parse envelope bytes and return root element."""
    return etree.fromstring(data)


# ---------- build_envelope ----------


class TestBuildEnvelope:
    def test_produces_valid_soap_xml(self):
        result = build_envelope("Tracker", "getWorkItemById", {"id": "WI-001"})
        root = _parse_envelope(result)
        assert root.tag == f"{{{NS_SOAP}}}Envelope"

        body = root.find(f"{{{NS_SOAP}}}Body")
        assert body is not None
        assert len(body) == 1

    def test_includes_session_header(self):
        session_elem = etree.Element("{http://ws.polarion.com/session}sessionID")
        session_elem.text = "abc123"

        result = build_envelope("Tracker", "getWorkItemById", {"id": "WI-001"}, session_header=session_elem)
        root = _parse_envelope(result)
        header = root.find(f"{{{NS_SOAP}}}Header")
        assert header is not None
        session = header.find("{http://ws.polarion.com/session}sessionID")
        assert session is not None
        assert session.text == "abc123"

    def test_no_session_header(self):
        result = build_envelope("Tracker", "getWorkItemById", {"id": "WI-001"})
        root = _parse_envelope(result)
        header = root.find(f"{{{NS_SOAP}}}Header")
        assert header is not None
        assert len(header) == 0

    def test_unknown_service_logs_warning(self, caplog):
        """Unknown service should log a warning and produce an envelope anyway."""
        import logging

        with caplog.at_level(logging.WARNING, logger="polarion.soap.envelope"):
            result = build_envelope("UnknownSvc", "someMethod", {"x": "1"})

        assert "UnknownSvc" in caplog.text
        assert "no known namespace" in caplog.text

        # Still produces valid XML
        root = _parse_envelope(result)
        assert root.tag == f"{{{NS_SOAP}}}Envelope"

    def test_params_appear_in_body(self):
        result = build_envelope("Session", "logIn", {"userName": "admin", "password": "secret"})
        root = _parse_envelope(result)
        body = root.find(f"{{{NS_SOAP}}}Body")
        method_elem = body[0]
        children = {child.tag.split("}")[-1] if "}" in child.tag else child.tag: child.text for child in method_elem}
        assert children["userName"] == "admin"
        assert children["password"] == "secret"


# ---------- _add_param ----------


class TestAddParam:
    def _make_parent(self) -> etree._Element:
        return etree.Element("parent")

    def test_none_produces_nil(self):
        parent = self._make_parent()
        _add_param(parent, "field", None)
        child = parent[0]
        assert child.get(f"{{{NS_XSI}}}nil") == "true"

    def test_nil_sentinel_produces_nil(self):
        parent = self._make_parent()
        _add_param(parent, "field", NIL)
        child = parent[0]
        assert child.get(f"{{{NS_XSI}}}nil") == "true"

    def test_str_value(self):
        parent = self._make_parent()
        _add_param(parent, "name", "Alice")
        assert parent[0].text == "Alice"

    def test_int_value(self):
        parent = self._make_parent()
        _add_param(parent, "count", 42)
        assert parent[0].text == "42"

    def test_float_value(self):
        parent = self._make_parent()
        _add_param(parent, "ratio", 3.14)
        assert parent[0].text == "3.14"

    def test_bool_true(self):
        parent = self._make_parent()
        _add_param(parent, "flag", True)
        assert parent[0].text == "true"

    def test_bool_false(self):
        parent = self._make_parent()
        _add_param(parent, "flag", False)
        assert parent[0].text == "false"

    def test_bytes_base64(self):
        parent = self._make_parent()
        raw = b"binary data"
        _add_param(parent, "attachment", raw)
        assert parent[0].text == base64.b64encode(raw).decode("ascii")

    def test_datetime_iso(self):
        parent = self._make_parent()
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        _add_param(parent, "created", dt)
        assert "2024-01-15" in parent[0].text
        assert "10:30:00" in parent[0].text

    def test_date_iso(self):
        parent = self._make_parent()
        d = date(2024, 6, 15)
        _add_param(parent, "dueDate", d)
        assert parent[0].text == "2024-06-15"

    def test_list_produces_multiple_elements(self):
        parent = self._make_parent()
        _add_param(parent, "item", ["a", "b", "c"])
        assert len(parent) == 3
        texts = [child.text for child in parent]
        assert texts == ["a", "b", "c"]

    def test_dict_nested(self):
        parent = self._make_parent()
        _add_param(parent, "config", {"key": "val", "num": "1"})
        container = parent[0]
        children = {child.tag: child.text for child in container}
        assert children["key"] == "val"
        assert children["num"] == "1"

    def test_dict_with_type_key_skips_type(self):
        parent = self._make_parent()
        _add_param(parent, "field", {"__type__": "SomeType", "id": "123"})
        container = parent[0]
        child_tags = [child.tag for child in container]
        assert "__type__" not in child_tags
        assert "id" in child_tags
