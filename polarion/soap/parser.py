"""SOAP response XML parsing.

Parses Polarion SOAP responses into Python dicts, handling nested structures,
arrays, and typed elements. Extracts SOAP faults as exceptions.
"""

from __future__ import annotations

import base64
import logging
from datetime import datetime
from typing import Any

from lxml import etree

from ..exceptions import PolarionApiError

logger = logging.getLogger(__name__)

# Namespaces used in responses
NS_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
NS_XSD = "http://www.w3.org/2001/XMLSchema"


def parse_response(content: bytes) -> Any:
    """Parse a SOAP response, extracting the body content.

    :param content: Raw XML response bytes
    :return: Parsed body content (dict, list, str, or None)
    :raises PolarionApiError: If the response contains a SOAP fault
    """
    root = etree.fromstring(content)

    # Check for SOAP fault
    fault = root.find(f".//{{{NS_SOAP}}}Fault")
    if fault is not None:
        fault_string = _get_text(fault, "faultstring") or "Unknown SOAP fault"
        fault_detail = _get_text(fault, "detail")
        msg = fault_string
        if fault_detail:
            msg += f": {fault_detail}"
        raise PolarionApiError(msg)

    # Extract body content
    body = root.find(f"{{{NS_SOAP}}}Body")
    if body is None:
        raise PolarionApiError("No SOAP Body found in response")

    # The response element is the first child of Body
    response_elem = body[0] if len(body) > 0 else None
    if response_elem is None:
        return None

    # The return value is typically in a child element
    # Polarion uses various naming: <*Return>, <*Result>, or direct content
    children = list(response_elem)
    if len(children) == 0:
        return response_elem.text
    if len(children) == 1:
        return _parse_element(children[0])

    # Multiple children → return the parsed response element
    return _parse_element(response_elem)


def parse_session_id(content: bytes) -> etree._Element | None:
    """Extract the session ID element from a SOAP response header.

    :param content: Raw XML response bytes
    :return: Session ID element, or None
    """
    root = etree.fromstring(content)
    return root.find(f".//{{{_NS_SESSION}}}sessionID")


_NS_SESSION = "http://ws.polarion.com/session"


def _get_text(elem: etree._Element, tag: str) -> str | None:
    """Get text content of a direct child element."""
    child = elem.find(tag)
    if child is not None:
        return child.text
    # Try without namespace
    for c in elem:
        if _local_name(c) == tag:
            return c.text
    return None


def _local_name(elem: etree._Element) -> str:
    """Get the local name of an element (without namespace)."""
    tag = elem.tag
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _is_nil(elem: etree._Element) -> bool:
    """Check if an element has xsi:nil='true'."""
    nil_val = elem.get(f"{{{NS_XSI}}}nil")
    return nil_val is not None and nil_val.lower() == "true"


def _parse_element(elem: etree._Element) -> Any:
    """Recursively parse an XML element into Python types.

    Returns:
    - None for nil elements
    - str for leaf text elements
    - dict for complex elements
    - list for repeated elements with same name
    - Attempts to detect dates, booleans, integers
    """
    if _is_nil(elem):
        return None

    children = list(elem)
    if not children:
        # Leaf node
        return _parse_text(elem.text)

    # Check if all children have the same tag → treat as array
    child_tags = [c.tag for c in children]
    if len(set(child_tags)) == 1 and len(children) > 1:
        return [_parse_element(c) for c in children]

    # Check for array-like structures where a single child name repeats
    # (e.g., <items><item>...</item><item>...</item></items>)
    result: dict[str, Any] = {}

    # Track if element itself has an 'unresolvable' attribute (Polarion pattern)
    if elem.get("unresolvable"):
        result["unresolvable"] = elem.get("unresolvable") == "true"

    tag_counts: dict[str, int] = {}
    for child in children:
        local = _local_name(child)
        tag_counts[local] = tag_counts.get(local, 0) + 1

    for child in children:
        local = _local_name(child)
        parsed = _parse_element(child)

        if tag_counts[local] > 1:
            # Multiple elements with same name → list
            if local not in result:
                result[local] = []
            result[local].append(parsed)
        else:
            result[local] = parsed

    return result


def _parse_text(text: str | None) -> Any:
    """Parse text content, attempting type detection."""
    if text is None:
        return None

    # Boolean
    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False

    # Try integer
    try:
        return int(text)
    except ValueError:
        pass

    # Try float (but not for strings that happen to have dots like URIs)
    if "." in text and not text.startswith("http") and not text.startswith("subterra"):
        try:
            return float(text)
        except ValueError:
            pass

    # Try datetime (ISO format)
    if len(text) >= 19 and "T" in text:
        try:
            # Handle timezone formats
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            pass

    return text
