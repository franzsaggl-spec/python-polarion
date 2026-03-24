"""v3 error hierarchy."""


class PolarionError(Exception):
    pass


class AuthError(PolarionError):
    pass


class NotFoundError(PolarionError):
    pass


class ValidationError(PolarionError):
    pass


class TransportError(PolarionError):
    pass


class ParsingError(PolarionError):
    pass


class ConflictError(PolarionError):
    pass
