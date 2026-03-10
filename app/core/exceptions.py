"""
Custom application exceptions.

All exceptions derive from AppException so that a single FastAPI
exception handler can convert them to consistent JSON responses.
"""


class AppException(Exception):
    """Base class for all application-level exceptions."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundException(AppException):
    """Raised when a requested resource does not exist in the database."""

    def __init__(self, resource: str, identifier) -> None:
        super().__init__(f"{resource} '{identifier}' was not found.", 404)


class ConflictException(AppException):
    """Raised when an operation violates a business rule or state constraint."""

    def __init__(self, message: str) -> None:
        super().__init__(message, 409)


class InsufficientSeatsException(AppException):
    """Raised when a guest requests more seats than are currently available."""

    def __init__(self, requested: int, available: int) -> None:
        super().__init__(
            f"Not enough seats: {requested} requested, only {available} available.",
            409,
        )


class QuotaExceededException(AppException):
    """Raised when the requested quota would exceed the total seat count."""

    def __init__(self, requested: int, total: int) -> None:
        super().__init__(
            f"Requested quota {requested} exceeds total seat count {total}.",
            422,
        )


class InvalidCredentialsException(AppException):
    """Raised when username or password does not match."""

    def __init__(self) -> None:
        super().__init__("Invalid username or password.", 401)


class TokenExpiredException(AppException):
    """Raised when the JWT token has passed its expiry time."""

    def __init__(self) -> None:
        super().__init__("Token has expired.", 401)


class InvalidTokenException(AppException):
    """Raised when the JWT token cannot be decoded or verified."""

    def __init__(self) -> None:
        super().__init__("Invalid token.", 401)


class UnauthorizedException(AppException):
    """Raised when a user lacks the required role for an action."""

    def __init__(self, message: str = "Insufficient permissions.") -> None:
        super().__init__(message, 403)


class ReservationExpiredException(AppException):
    """Raised when an operation targets a reservation that has already expired."""

    def __init__(self, reservation_id: int) -> None:
        super().__init__(f"Reservation {reservation_id} has expired.", 410)


class ReservationAlreadyCheckedInException(AppException):
    """Raised when a check-in is attempted on an already checked-in reservation."""

    def __init__(self, reservation_id: int) -> None:
        super().__init__(f"Reservation {reservation_id} has already been checked in.", 409)