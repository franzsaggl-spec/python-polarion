"""Tests for polarion.soap.parser — SOAP response XML parsing."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from lxml import etree

from polarion.exceptions import PolarionApiError
from polarion.soap.parser import _parse_element, _parse_text, parse_response

NS_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"


def _soap_envelope(body_content: str) -> bytes:
    """Build a minimal SOAP envelope with the given body content."""
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f"<soapenv:Envelope "
        f'xmlns:soapenv="{NS_SOAP}" '
        f'xmlns:xsi="{NS_XSI}">'
        f"<soapenv:Body>{body_content}</soapenv:Body>"
        f"</soapenv:Envelope>"
    ).encode("utf-8")


# ---------- parse_response ----------


class TestParseResponse:
    def test_soap_fault_raises(self):
        xml = _soap_envelope("<soapenv:Fault><faultstring>Access denied</faultstring></soapenv:Fault>")
        with pytest.raises(PolarionApiError, match="Access denied"):
            parse_response(xml)

    def test_soap_fault_with_detail(self):
        xml = _soap_envelope(
            "<soapenv:Fault><faultstring>Server error</faultstring><detail>Stack trace here</detail></soapenv:Fault>"
        )
        with pytest.raises(PolarionApiError, match="Server error.*Stack trace"):
            parse_response(xml)

    def test_no_body_raises(self):
        xml = (
            f'<?xml version="1.0" encoding="UTF-8"?><soapenv:Envelope xmlns:soapenv="{NS_SOAP}"></soapenv:Envelope>'
        ).encode("utf-8")
        with pytest.raises(PolarionApiError, match="No SOAP Body"):
            parse_response(xml)

    def test_invalid_xml_raises(self):
        with pytest.raises(PolarionApiError, match="Server returned invalid XML"):
            parse_response(b"<not-valid-xml")

    def test_empty_response_returns_none(self):
        xml = _soap_envelope("<getResponse/>")
        result = parse_response(xml)
        assert result is None

    def test_single_child_returns_parsed(self):
        xml = _soap_envelope("<getResponse><result>hello</result></getResponse>")
        result = parse_response(xml)
        assert result == "hello"

    def test_multiple_children_returns_parsed_dict(self):
        xml = _soap_envelope("<getResponse><name>Alice</name><role>admin</role></getResponse>")
        result = parse_response(xml)
        assert isinstance(result, dict)
        assert result["name"] == "Alice"
        assert result["role"] == "admin"


# ---------- _parse_element ----------


class TestParseElement:
    def test_nil_returns_none(self):
        elem = etree.fromstring(f'<item xsi:nil="true" xmlns:xsi="{NS_XSI}"/>')
        assert _parse_element(elem) is None

    def test_leaf_text_returns_str(self):
        elem = etree.fromstring("<name>hello</name>")
        assert _parse_element(elem) == "hello"

    def test_array_same_tags_returns_list(self):
        xml = "<items><item>a</item><item>b</item><item>c</item></items>"
        elem = etree.fromstring(xml)
        result = _parse_element(elem)
        assert result == ["a", "b", "c"]

    def test_mixed_children_returns_dict(self):
        xml = "<item><name>Alice</name><age>30</age></item>"
        elem = etree.fromstring(xml)
        result = _parse_element(elem)
        assert isinstance(result, dict)
        assert result["name"] == "Alice"
        assert result["age"] == "30"

    def test_unresolvable_attribute(self):
        xml = '<item unresolvable="true"><name>test</name></item>'
        elem = etree.fromstring(xml)
        result = _parse_element(elem)
        assert isinstance(result, dict)
        assert result["unresolvable"] is True

    def test_unresolvable_false(self):
        xml = '<item unresolvable="false"><name>test</name></item>'
        elem = etree.fromstring(xml)
        result = _parse_element(elem)
        assert isinstance(result, dict)
        assert result["unresolvable"] is False

    def test_repeated_child_among_others_returns_list_in_dict(self):
        xml = "<root><name>x</name><tag>a</tag><tag>b</tag></root>"
        elem = etree.fromstring(xml)
        result = _parse_element(elem)
        assert result["name"] == "x"
        assert result["tag"] == ["a", "b"]


# ---------- _parse_text ----------


class TestParseText:
    def test_none_returns_none(self):
        assert _parse_text(None) is None

    def test_true_string(self):
        assert _parse_text("true") is True
        assert _parse_text("True") is True
        assert _parse_text("TRUE") is True

    def test_false_string(self):
        assert _parse_text("false") is False
        assert _parse_text("False") is False

    def test_numeric_string_remains_string(self):
        assert _parse_text("42") == "42"
        assert isinstance(_parse_text("42"), str)

    def test_float_string_remains_string(self):
        assert _parse_text("3.14") == "3.14"
        assert isinstance(_parse_text("3.14"), str)

    def test_iso_datetime(self):
        result = _parse_text("2024-01-15T10:30:00+00:00")
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1

    def test_iso_datetime_with_z(self):
        result = _parse_text("2024-01-15T10:30:00Z")
        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc

    def test_plain_text_unchanged(self):
        assert _parse_text("hello world") == "hello world"

    def test_short_text_not_datetime(self):
        assert _parse_text("T") == "T"
        assert _parse_text("short") == "short"
