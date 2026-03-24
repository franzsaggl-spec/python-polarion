"""SOAP envelope construction using lxml.

Builds SOAP 1.1 envelopes for Polarion web services. Handles nested
parameters, arrays, typed elements, nillable values, and binary data.
"""

from __future__ import annotations

import base64
import logging
from datetime import date, datetime
from typing import Any

from lxml import etree

logger = logging.getLogger(__name__)

# SOAP / Polarion namespaces
NS_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
NS_XSD = "http://www.w3.org/2001/XMLSchema"
NS_SESSION = "http://ws.polarion.com/session"

# Common Polarion service namespaces
SERVICE_NAMESPACES: dict[str, dict[str, str]] = {
    "Session": {
        "ns": "http://ws.polarion.com/SessionWebService-impl",
        "types": "http://ws.polarion.com/SessionWebService-types",
    },
    "Tracker": {
        "ns": "http://ws.polarion.com/TrackerWebService-impl",
        "types": "http://ws.polarion.com/TrackerWebService-types",
    },
    "Project": {
        "ns": "http://ws.polarion.com/ProjectWebService-impl",
        "types": "http://ws.polarion.com/ProjectWebService-types",
    },
    "TestManagement": {
        "ns": "http://ws.polarion.com/TestManagementWebService-impl",
        "types": "http://ws.polarion.com/TestManagementWebService-types",
    },
    "Planning": {
        "ns": "http://ws.polarion.com/PlanningWebService-impl",
        "types": "http://ws.polarion.com/PlanningWebService-types",
    },
    "Builder": {
        "ns": "http://ws.polarion.com/BuilderWebService-impl",
        "types": "http://ws.polarion.com/BuilderWebService-types",
    },
    "Security": {
        "ns": "http://ws.polarion.com/SecurityWebService-impl",
        "types": "http://ws.polarion.com/SecurityWebService-types",
    },
}

# Sentinel for nil/null values
NIL = object()


def build_envelope(
    service: str,
    method: str,
    params: dict[str, Any],
    session_header: etree._Element | None = None,
) -> bytes:
    """Build a complete SOAP 1.1 envelope.

    :param service: Service name (e.g. "Tracker", "Session")
    :param method: Method name (e.g. "getWorkItemById")
    :param params: Method parameters as a dict
    :param session_header: Session ID XML element to include in header
    :return: Serialized XML bytes
    """
    nsmap = {
        "soapenv": NS_SOAP,
        "xsi": NS_XSI,
        "xsd": NS_XSD,
    }

    svc_ns = SERVICE_NAMESPACES.get(service)
    if svc_ns is None:
        logger.warning("Service '%s' has no known namespace; SOAP envelope may be malformed", service)
        svc_ns = {}
    impl_ns = svc_ns.get("ns", "")
    if impl_ns:
        nsmap["impl"] = impl_ns

    envelope = etree.Element(f"{{{NS_SOAP}}}Envelope", nsmap=nsmap)

    # Header (with session ID if available)
    header = etree.SubElement(envelope, f"{{{NS_SOAP}}}Header")
    if session_header is not None:
        header.append(session_header)

    # Body
    body = etree.SubElement(envelope, f"{{{NS_SOAP}}}Body")
    method_elem = etree.SubElement(body, f"{{{impl_ns}}}{method}" if impl_ns else method)

    # Add parameters
    for key, value in params.items():
        _add_param(method_elem, key, value)

    return etree.tostring(envelope, xml_declaration=True, encoding="UTF-8")


def _add_param(parent: etree._Element, name: str, value: Any) -> None:
    """Add a parameter element to the parent XML element.

    Handles:
    - None → element with xsi:nil="true"
    - NIL sentinel → element with xsi:nil="true"
    - str, int, float, bool → text content
    - bytes → base64 encoded
    - datetime/date → ISO format
    - list → multiple elements with same name
    - dict → nested elements (supports __type__ key for typed elements)
    - Nested structures recursively
    """
    if value is NIL:
        elem = etree.SubElement(parent, name)
        elem.set(f"{{{NS_XSI}}}nil", "true")
        return

    if value is None:
        elem = etree.SubElement(parent, name)
        elem.set(f"{{{NS_XSI}}}nil", "true")
        return

    if isinstance(value, list):
        for item in value:
            _add_param(parent, name, item)
        return

    elem = etree.SubElement(parent, name)

    if isinstance(value, bool):
        elem.text = "true" if value else "false"
    elif isinstance(value, (int, float)):
        elem.text = str(value)
    elif isinstance(value, str):
        elem.text = value
    elif isinstance(value, bytes):
        elem.text = base64.b64encode(value).decode("ascii")
    elif isinstance(value, datetime):
        elem.text = value.strftime("%Y-%m-%dT%H:%M:%S.%f%z") or value.isoformat()
    elif isinstance(value, date):
        elem.text = value.isoformat()
    elif isinstance(value, dict):
        for k, v in value.items():
            if k == "__type__":
                continue  # metadata, not a field
            _add_param(elem, k, v)
    else:
        elem.text = str(value)
