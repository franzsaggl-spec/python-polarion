"""SOAP client internals for Polarion web services."""

from .client import SoapClient
from .constants import NS_SESSION, NS_SOAP, NS_XSD, NS_XSI

__all__ = ["SoapClient", "NS_SOAP", "NS_XSI", "NS_XSD", "NS_SESSION"]
