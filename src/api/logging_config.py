"""Sanitized JSON request logs, one line per request.

Never log payloads, credentials, customer records, SQL or exception text.
"""

import json
import logging
from datetime import datetime, timezone

LOGGER = logging.getLogger("banking.api")


def configure_logging():
    LOGGER.setLevel(logging.INFO)
    if not LOGGER.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        LOGGER.addHandler(handler)
    LOGGER.propagate = False


def log_request(correlation_id: str, operation: str, status_code: int, duration_ms: float):
    if status_code >= 500:
        outcome = "server_error"
        level = logging.ERROR
    elif status_code >= 400:
        outcome = "client_error"
        level = logging.WARNING
    else:
        outcome = "success"
        level = logging.INFO
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": logging.getLevelName(level),
        "correlation_id": correlation_id,
        "operation": operation,
        "outcome": outcome,
        "duration_ms": round(duration_ms, 2),
        "status_code": status_code,
    }
    LOGGER.log(level, json.dumps(record, separators=(",", ":")))
