"""Custom exception hierarchy for the Polarion client library."""


class PolarionError(Exception):
    """Base exception for all Polarion client errors."""


class PolarionAuthError(PolarionError):
    """Raised when authentication or session creation fails."""


class PolarionNotFoundError(PolarionError):
    """Raised when a requested resource (workitem, project, plan, etc.) cannot be found."""


class PolarionConnectionError(PolarionError):
    """Raised when a WSDL service is unavailable or a network error occurs."""


class PolarionConfigError(PolarionError):
    """Raised when configuration is invalid or missing required fields."""


class PolarionApiError(PolarionError):
    """Raised when a SOAP API call fails."""


class PolarionFieldError(PolarionError):
    """Raised when an invalid field, custom field key, or argument is used."""
