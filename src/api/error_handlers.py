"""Small, predictable API error contract.

Every error returns code, message and correlation_id. Internal details stay out
of client responses. Business rules are still owned by the domain and service.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException


class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def error_response(request: Request, code: str, message: str, status_code: int):
    cid = getattr(request.state, "correlation_id", "unknown")
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message, "correlation_id": cid},
        headers={"X-Correlation-ID": cid},
    )


def register_error_handlers(app: FastAPI):
    @app.exception_handler(APIError)
    async def api_error(request: Request, exc: APIError):
        return error_response(request, exc.code, exc.message, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def bad_request(request: Request, exc: RequestValidationError):
        # Do not echo request bodies or Pydantic's input values.
        return error_response(request, "VALIDATION_ERROR", "Invalid request data", 422)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            return error_response(request, "NOT_FOUND", "Not found", 404)
        if exc.status_code == 503:
            return error_response(request, "DEPENDENCY_UNAVAILABLE", "Database unavailable", 503)
        if exc.status_code == 405:
            return error_response(request, "METHOD_NOT_ALLOWED", "Method not allowed", 405)
        if exc.status_code == 422:
            return error_response(request, "VALIDATION_ERROR", "Invalid request data", 422)
        if exc.status_code == 409:
            return error_response(request, "CONFLICT", "Conflict", 409)
        return error_response(request, "INTERNAL_ERROR", "Internal server error", 500)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError):
        from sqlalchemy.exc import IntegrityError
        if isinstance(exc, IntegrityError):
            return error_response(request, "CONFLICT", "Database constraint conflict", 409)
        return error_response(request, "DEPENDENCY_UNAVAILABLE", "Database unavailable", 503)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        return error_response(request, "INTERNAL_ERROR", "Internal server error", 500)
