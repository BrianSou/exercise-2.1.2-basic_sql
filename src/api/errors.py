"""Map service and repository failures to safe API errors."""

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.api.error_handlers import APIError


def service_error(exc: Exception):
    if isinstance(exc, ValueError):
        message = str(exc)
        if message == "Customer not found":
            raise APIError("CUSTOMER_NOT_FOUND", "Customer not found", 404) from None
        if message == "Complaint not found":
            raise APIError("COMPLAINT_NOT_FOUND", "Complaint not found", 404) from None
        if message == "Complaint ID already exists":
            raise APIError("CONFLICT", "Complaint ID already exists", 409) from None
        if message.startswith(("Cannot change status", "Complaint status changed", "ESCALATED is not")):
            # No user-controlled error details are returned.
            raise APIError("INVALID_STATUS_TRANSITION", "Status change not allowed", 409) from None
        raise APIError("VALIDATION_ERROR", "Invalid request data", 422) from None
    if isinstance(exc, IntegrityError):
        raise APIError("CONFLICT", "Database constraint conflict", 409) from None
    if isinstance(exc, SQLAlchemyError):
        raise APIError("DEPENDENCY_UNAVAILABLE", "Database unavailable", 503) from None
    raise exc
