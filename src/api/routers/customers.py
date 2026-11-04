"""Customer read endpoints. All database access goes through repositories."""

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError

from src.api.dependencies import get_complaint_service
from src.api.errors import service_error
from src.api.schemas import ComplaintResponse, CustomerResponse
from src.services.complaint_service import ComplaintService

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/{id}", response_model=CustomerResponse, responses={404: {"description": "Customer not found"}, 503: {"description": "Database unavailable"}})
def get_customer(id: str, service: ComplaintService = Depends(get_complaint_service)):
    try:
        customer = service.get_customer(id)
    except SQLAlchemyError as exc:
        service_error(exc)
    if customer is None:
        service_error(ValueError("Customer not found"))
    return customer


@router.get("/{id}/complaints", response_model=list[ComplaintResponse], responses={404: {"description": "Customer not found"}, 503: {"description": "Database unavailable"}})
def get_customer_complaints(
    id: str, service: ComplaintService = Depends(get_complaint_service)
):
    try:
        return service.get_for_customer(id)
    except (ValueError, SQLAlchemyError) as exc:
        service_error(exc)
