"""Build the real service. Tests can pass fake repositories instead."""

from src.data.database_manager import DatabaseManager
from src.data.customer_repository import CustomerRepository
from src.data.account_repository import AccountRepository
from src.data.complaint_repository import ComplaintRepository
from src.services.complaint_service import ComplaintService


def build_complaint_service(db=None):
    db = db or DatabaseManager()
    return ComplaintService(
        complaint_repo=ComplaintRepository(db),
        customer_repo=CustomerRepository(db),
        account_repo=AccountRepository(db),
    )
