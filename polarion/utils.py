"""Utility functions for Polarion data processing."""

from __future__ import annotations

import re
from abc import ABC
from html.parser import HTMLParser
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from texttable import Texttable

if TYPE_CHECKING:
    from polarion.project import Project

_HTML_TAG_RE = re.compile("<.*?>")


def ensure_list(value: Any) -> list:
    """Normalize a value that may be a single item or a list into a list.

    SOAP responses often return a single dict when there is one result
    and a list when there are multiple. This helper eliminates the
    ``x if isinstance(x, list) else [x]`` pattern used throughout.
    """
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def extract_id(data: Any, key: str = "id", default: str = "") -> str:
    """Extract an ID string from a SOAP value that may be a dict or a plain string."""
    if data is None:
        return default
    if isinstance(data, dict):
        return data.get(key, default)
    return str(data)


class DescriptionParser(HTMLParser, ABC):
    """HTML parser for Polarion descriptions.

    Strips HTML tags, renders tables in text format, resolves
    Polarion work item links, and extracts formulas.

    :param polarion_project: Project instance for resolving long-form links
    """

    def __init__(self, polarion_project: Project | None = None) -> None:
        super().__init__()
        self._polarion_project = polarion_project
        self._data = ""
        self._table_start: tuple[int, int] | None = None
        self._table_end: tuple[int, int] | None = None

    @property
    def data(self) -> str:
        """The parsed plain-text data."""
        return self._data

    def reset(self) -> None:
        super().reset()
        self._data = ""
        self._table_start = None
        self._table_end = None

    def handle_data(self, data: str) -> None:
        if self._table_start is None:
            self._data += data

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)

        if tag == "span" and "class" in attributes:
            if attributes["class"] == "polarion-rte-link":
                self._handle_polarion_rte_link(attributes)
            elif attributes["class"] == "polarion-rte-formula":
                self._handle_polarion_rte_formula(attributes)

        if tag == "table":
            self._table_start = self.getpos()

    def handle_endtag(self, tag: str) -> None:
        if tag == "table":
            self._handle_table()

    def _handle_table(self) -> None:
        self._table_end = self.getpos()
        table_content = self.rawdata.split("\n")
        correct_lines = table_content[self._table_start[0] - 1 : self._table_end[0]]
        table = ElementTree.XML("".join(correct_lines))
        content: list[list[str | None]] = []
        for tr in table.iter("tr"):
            content.append([])
            for th in tr.iter("th"):
                content[-1].append(th.text)
            for td in tr.iter("td"):
                content[-1].append(td.text)
        self._data += Texttable().add_rows(content).draw()
        self._table_start = None
        self._table_end = None

    def _handle_polarion_rte_link(self, attributes: dict[str, str | None]) -> None:
        if attributes["data-option-id"] == "short" or (
            attributes["data-option-id"] == "long" and self._polarion_project is None
        ):
            self._data += attributes["data-item-id"]
        else:
            linked_item = self._polarion_project.get_workitem(attributes["data-item-id"])
            self._data += str(linked_item)

    def _handle_polarion_rte_formula(self, attributes: dict[str, str | None]) -> None:
        self._data += attributes["data-source"]


def save_bytes_as_pdf(input_bytes: bytes, filename: str) -> None:
    """Save bytes as a PDF file.

    :param input_bytes: PDF content
    :param filename: Output file path
    """
    if not filename.endswith(".pdf"):
        filename += ".pdf"
    with open(filename, "wb") as f:
        f.write(input_bytes)


def strip_html(raw_html: str) -> str:
    """Strip all HTML tags, leaving plain text.

    :param raw_html: HTML string
    :return: Plain text
    """
    return _HTML_TAG_RE.sub("", raw_html)
