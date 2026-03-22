"""Tests for utility functions in polarion.utils."""

import os
import pytest

from polarion.utils import strip_html, save_bytes_as_pdf, DescriptionParser


# ---------------------------------------------------------------------------
# strip_html
# ---------------------------------------------------------------------------

class TestStripHtml:
    def test_simple_tags(self):
        assert strip_html('<p>Hello</p>') == 'Hello'

    def test_nested_tags(self):
        assert strip_html('<div><p><b>Bold</b> text</p></div>') == 'Bold text'

    def test_empty_string(self):
        assert strip_html('') == ''

    def test_no_tags(self):
        assert strip_html('plain text') == 'plain text'

    def test_self_closing_tags(self):
        result = strip_html('line1<br/>line2')
        assert result == 'line1line2'

    def test_tags_with_attributes(self):
        result = strip_html('<a href="http://example.com">link</a>')
        assert result == 'link'

    def test_multiple_tags(self):
        result = strip_html('<h1>Title</h1><p>Paragraph</p>')
        assert result == 'TitleParagraph'


# ---------------------------------------------------------------------------
# save_bytes_as_pdf
# ---------------------------------------------------------------------------

class TestSaveBytesAsPdf:
    def test_saves_bytes_with_pdf_extension(self, tmp_path):
        filepath = str(tmp_path / 'output.pdf')
        content = b'%PDF-1.4 fake pdf content'
        save_bytes_as_pdf(content, filepath)

        assert os.path.exists(filepath)
        with open(filepath, 'rb') as f:
            assert f.read() == content

    def test_adds_pdf_extension_when_missing(self, tmp_path):
        filepath = str(tmp_path / 'output')
        content = b'%PDF-1.4 fake pdf content'
        save_bytes_as_pdf(content, filepath)

        expected_path = filepath + '.pdf'
        assert os.path.exists(expected_path)
        with open(expected_path, 'rb') as f:
            assert f.read() == content

    def test_does_not_double_pdf_extension(self, tmp_path):
        filepath = str(tmp_path / 'output.pdf')
        content = b'some bytes'
        save_bytes_as_pdf(content, filepath)

        # Should not create output.pdf.pdf
        double_path = filepath + '.pdf'
        assert not os.path.exists(double_path)
        assert os.path.exists(filepath)


# ---------------------------------------------------------------------------
# DescriptionParser
# ---------------------------------------------------------------------------

class TestDescriptionParser:
    def _parse(self, html, project=None):
        """Helper to instantiate parser, feed HTML, and return data."""
        # DescriptionParser is ABC, so we need a concrete subclass
        class ConcreteParser(DescriptionParser):
            pass

        parser = ConcreteParser(project)
        parser.feed(html)
        return parser.data

    def test_plain_text_in_tags(self):
        result = self._parse('<p>Hello World</p>')
        assert result == 'Hello World'

    def test_multiple_paragraphs(self):
        result = self._parse('<p>First</p><p>Second</p>')
        assert 'First' in result
        assert 'Second' in result

    def test_nested_tags_extracts_text(self):
        result = self._parse('<div><span>inner</span></div>')
        assert 'inner' in result

    def test_empty_html(self):
        result = self._parse('')
        assert result == ''

    def test_reset_clears_data(self):
        class ConcreteParser(DescriptionParser):
            pass

        parser = ConcreteParser()
        parser.feed('<p>data</p>')
        assert parser.data == 'data'
        parser.reset()
        assert parser.data == ''

    def test_formula_extraction(self):
        html = '<span class="polarion-rte-formula" data-source="E=mc^2"></span>'
        result = self._parse(html)
        assert 'E=mc^2' in result

    def test_polarion_link_short(self):
        html = '<span class="polarion-rte-link" data-option-id="short" data-item-id="WI-123"></span>'
        result = self._parse(html)
        assert 'WI-123' in result
