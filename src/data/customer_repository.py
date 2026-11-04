"""Read customers with SQLAlchemy."""
from src.data.orm_models import CustomerRow


class CustomerRepository:
    def __init__(self, db):
        self.db = db

    def get_by_id(self, customer_id):
        with self.db.session() as session:
            row = session.get(CustomerRow, customer_id)
            if row is None:
                return None
            return {
                "customer_id": row.customer_id,
                "first_name": row.first_name,
                "last_name": row.last_name,
                "email": row.email,
            }
