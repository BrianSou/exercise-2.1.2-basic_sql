"""Request and response shapes for the public API.

Pydantic validates incoming JSON before a service method runs.
"""

from pydantic import BaseModel, ConfigDict, Field

from src.domain.models import ComplaintCategory, ComplaintPriority, ComplaintStatus


class ErrorResponse(BaseModel):
    code: str
    message: str
    correlation_id: str


class HealthResponse(BaseModel):
    status: str


class CustomerResponse(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    email: str | None = None


class ComplaintResponse(BaseModel):
    complaint_id: str
    customer_id: str
    account_id: str | None = None
    channel: str | None = None
    category: str
    complaint_text: str | None = None
    priority: str | None = None
    status: str
    received_at: str
    assigned_analyst_id: str | None = None


class CreateComplaintRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    complaint_id: str = Field(min_length=1, max_length=10)
    customer_id: str = Field(min_length=1, max_length=10)
    category: ComplaintCategory
    priority: ComplaintPriority
    created_by: str = Field(min_length=1, max_length=10)
    account_id: str | None = Field(default=None, min_length=1, max_length=10)
    complaint_text: str = Field(default="", max_length=5000)
    channel: str = Field(default="Web", min_length=1, max_length=20)
    assigned_analyst_id: str | None = Field(default=None, min_length=1, max_length=10)


class UpdateStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: ComplaintStatus
    changed_by: str = Field(min_length=1, max_length=10)
    comments: str | None = Field(default=None, max_length=2000)
