"""Tests for polarion/types.py dataclasses."""

from polarion.types import (
    Approval,
    AttachmentInfo,
    CustomFieldValue,
    EnumOption,
    HyperlinkInfo,
    LinkedItem,
    PdfProperties,
    TestStep,
    TestStepResult,
    TextContent,
)


class TestTextContent:
    def test_to_soap(self):
        tc = TextContent(content="hello", content_type="text/html")
        result = tc.to_soap()
        assert result == {"type": "text/html", "content": "hello", "contentLossy": False}

    def test_from_soap(self):
        data = {"content": "hello", "type": "text/plain", "contentLossy": True}
        tc = TextContent.from_soap(data)
        assert tc.content == "hello"
        assert tc.content_type == "text/plain"
        assert tc.content_lossy is True

    def test_from_soap_none(self):
        assert TextContent.from_soap(None) is None

    def test_from_soap_defaults(self):
        tc = TextContent.from_soap({"content": "x"})
        assert tc.content_type == "text/html"
        assert tc.content_lossy is False

    def test_roundtrip(self):
        original = TextContent(content="test", content_type="text/plain", content_lossy=True)
        restored = TextContent.from_soap(original.to_soap())
        assert restored.content == original.content
        assert restored.content_type == original.content_type
        assert restored.content_lossy == original.content_lossy


class TestEnumOption:
    def test_to_soap(self):
        eo = EnumOption(id="open")
        assert eo.to_soap() == {"id": "open"}

    def test_from_soap_dict(self):
        eo = EnumOption.from_soap({"id": "open", "name": "Open"})
        assert eo.id == "open"
        assert eo.name == "Open"

    def test_from_soap_string(self):
        eo = EnumOption.from_soap("open")
        assert eo.id == "open"

    def test_from_soap_none(self):
        assert EnumOption.from_soap(None) is None

    def test_from_soap_empty_dict(self):
        eo = EnumOption.from_soap({})
        assert eo.id == ""


class TestLinkedItem:
    def test_from_soap(self):
        data = {"role": {"id": "verifies"}, "workItemURI": "subterra:uri", "suspect": True}
        li = LinkedItem.from_soap(data)
        assert li.role == "verifies"
        assert li.workitem_uri == "subterra:uri"
        assert li.suspect is True

    def test_from_soap_string_role(self):
        li = LinkedItem.from_soap({"role": "verifies", "workItemURI": "uri"})
        assert li.role == "verifies"

    def test_from_soap_none(self):
        assert LinkedItem.from_soap(None) is None


class TestApproval:
    def test_from_soap(self):
        data = {"user": {"id": "admin"}, "status": {"id": "approved"}}
        a = Approval.from_soap(data)
        assert a.user_id == "admin"
        assert a.status == "approved"

    def test_from_soap_string_user(self):
        a = Approval.from_soap({"user": "admin", "status": "waiting"})
        assert a.user_id == "admin"
        assert a.status == "waiting"

    def test_from_soap_none(self):
        assert Approval.from_soap(None) is None


class TestCustomFieldValue:
    def test_to_soap(self):
        cf = CustomFieldValue(key="myfield", value=42)
        assert cf.to_soap() == {"key": "myfield", "value": 42}

    def test_from_soap(self):
        cf = CustomFieldValue.from_soap({"key": "myfield", "value": "val"})
        assert cf.key == "myfield"
        assert cf.value == "val"

    def test_from_soap_none(self):
        assert CustomFieldValue.from_soap(None) is None

    def test_roundtrip(self):
        original = CustomFieldValue(key="test", value="hello")
        restored = CustomFieldValue.from_soap(original.to_soap())
        assert restored.key == original.key
        assert restored.value == original.value


class TestAttachmentInfo:
    def test_from_soap(self):
        data = {"id": "att1", "fileName": "test.pdf", "title": "Test", "url": "http://x", "length": 1024}
        ai = AttachmentInfo.from_soap(data)
        assert ai.id == "att1"
        assert ai.file_name == "test.pdf"
        assert ai.title == "Test"
        assert ai.url == "http://x"
        assert ai.length == 1024

    def test_from_soap_none(self):
        assert AttachmentInfo.from_soap(None) is None

    def test_from_soap_empty(self):
        ai = AttachmentInfo.from_soap({})
        assert ai.id == ""
        assert ai.file_name == ""


class TestHyperlinkInfo:
    def test_from_soap(self):
        data = {"uri": "http://example.com", "role": {"id": "external reference"}}
        hi = HyperlinkInfo.from_soap(data)
        assert hi.uri == "http://example.com"
        assert hi.role == "external reference"

    def test_from_soap_string_role(self):
        hi = HyperlinkInfo.from_soap({"uri": "http://x", "role": "internal"})
        assert hi.role == "internal"

    def test_from_soap_none(self):
        assert HyperlinkInfo.from_soap(None) is None


class TestTestStep:
    def test_from_parsed(self):
        ts = TestStep.from_parsed(["step", "expected"], ["do thing", "see result"])
        assert ts.values == {"step": "do thing", "expected": "see result"}

    def test_from_parsed_empty(self):
        ts = TestStep.from_parsed([], [])
        assert ts.values == {}


class TestTestStepResult:
    def test_from_soap(self):
        data = {"result": {"id": "passed"}, "comment": {"content": "ok"}}
        tsr = TestStepResult.from_soap(data)
        assert tsr.result == "passed"
        assert tsr.comment == "ok"

    def test_from_soap_string_result(self):
        tsr = TestStepResult.from_soap({"result": "failed", "comment": "bad"})
        assert tsr.result == "failed"
        assert tsr.comment == "bad"

    def test_from_soap_none(self):
        assert TestStepResult.from_soap(None) is None


class TestPdfProperties:
    def test_defaults(self):
        pdf = PdfProperties()
        assert pdf.paper_size == "A4"
        assert pdf.orientation == "Portrait"

    def test_to_soap(self):
        pdf = PdfProperties(paper_size="Letter", orientation="Landscape")
        result = pdf.to_soap()
        assert result["paperSize"] == "Letter"
        assert result["orientation"] == "Landscape"
        assert result["fitToPageWidth"] is True

    def test_to_soap_all_fields(self):
        pdf = PdfProperties()
        result = pdf.to_soap()
        expected_keys = {
            "paperSize",
            "orientation",
            "fitToPageWidth",
            "markOptionalFields",
            "generateBookmarks",
            "updateLinkedItems",
        }
        assert set(result.keys()) == expected_keys
