"""FastAPI application with health, complaint routes and safe request logging."""

import re
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request

from src.api.error_handlers import error_response, register_error_handlers
from src.api.logging_config import configure_logging, log_request
from src.api.routers import complaints, customers, health
from src.api.schemas import ErrorResponse

# A caller may supply a correlation ID, but not an arbitrarily long or unsafe one.
SAFE_ID = re.compile(r"[A-Za-z0-9._-]{1,64}\Z")


def create_app():
    configure_logging()
    app = FastAPI(
        title="Banking Complaint API", version="0.3.0",
        responses={
            404: {"model": ErrorResponse, "description": "Record not found"},
            409: {"model": ErrorResponse, "description": "Business conflict"},
            422: {"model": ErrorResponse, "description": "Invalid request data"},
            503: {"model": ErrorResponse, "description": "Dependency unavailable"},
        },
    )
    register_error_handlers(app)

    @app.middleware("http")
    async def request_logging(request: Request, call_next):
        supplied = request.headers.get("X-Correlation-ID", "")
        correlation_id = supplied if SAFE_ID.fullmatch(supplied) else str(uuid4())
        request.state.correlation_id = correlation_id
        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # Catch anything not handled by FastAPI. Never return tracebacks.
            response = error_response(request, "INTERNAL_ERROR", "Internal server error", 500)
        response.headers["X-Correlation-ID"] = correlation_id
        route = request.scope.get("route")
        route_name = getattr(route, "path", "unmatched")
        operation = f"{request.method} {route_name}"
        log_request(correlation_id, operation, response.status_code,
                    (perf_counter() - started) * 1000)
        return response

    app.include_router(health.router)
    app.include_router(customers.router)
    app.include_router(complaints.router)
    return app


app = create_app()
