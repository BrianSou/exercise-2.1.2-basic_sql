"""Complaint routes call ComplaintService, which owns the business workflow."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.exc import SQLAlchemyError

from src.api.dependencies import get_complaint_service
from src.api.errors import service_error
from src.api.schemas import ComplaintResponse, CreateComplaintRequest, UpdateStatusRequest
from src.services.complaint_service import ComplaintService

router = APIRouter(prefix="/complaints", tags=["complaints"])


@router.get("/{id}", response_model=ComplaintResponse, responses={404: {"description": "Complaint not found"}, 503: {"description": "Database unavailable"}})
def get_complaint(id: str, service: ComplaintService = Depends(get_complaint_service)):
    try:
        complaint = service.get_complaint(id)
    except SQLAlchemyError as exc:
        service_error(exc)
    if complaint is None:
        service_error(ValueError("Complaint not found"))
    return complaint


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED, responses={404: {"description": "Customer not found"}, 409: {"description": "Duplicate ID or database conflict"}, 422: {"description": "Invalid input"}, 503: {"description": "Database unavailable"}})
def create_complaint(
    body: CreateComplaintRequest,
    response: Response,
    service: ComplaintService = Depends(get_complaint_service),
):
    try:
        created = service.create_complaint(
            complaint_id=body.complaint_id,
            customer_id=body.customer_id,
            category=body.category,
            priority=body.priority,
            created_by=body.created_by,
            account_id=body.account_id,
            complaint_text=body.complaint_text,
            channel=body.channel,
            assigned_analyst_id=body.assigned_analyst_id,
        )
        response.headers["Location"] = f"/complaints/{created['complaint_id']}"
        return created
    except (ValueError, SQLAlchemyError) as exc:
        service_error(exc)


@router.patch("/{id}/status", response_model=ComplaintResponse, responses={404: {"description": "Complaint not found"}, 409: {"description": "Blocked status change"}, 422: {"description": "Invalid input"}, 503: {"description": "Database unavailable"}})
def change_status(
    id: str,
    body: UpdateStatusRequest,
    service: ComplaintService = Depends(get_complaint_service),
):
    try:
        return service.change_status(
            complaint_id=id,
            new_status=body.status,
            changed_by=body.changed_by,
            comments=body.comments,
        )
    except (ValueError, SQLAlchemyError) as exc:
        service_error(exc)
