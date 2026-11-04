"""Read accounts with SQLAlchemy."""
from sqlalchemy import select
from src.data.orm_models import AccountRow


class AccountRepository:
    def __init__(self, db):
        self.db = db

    def get_for_customer(self, customer_id):
        with self.db.session() as session:
            rows = session.scalars(
                select(AccountRow)
                .where(AccountRow.customer_id == customer_id)
                .order_by(AccountRow.account_id)
            ).all()
            return [
                {
                    "account_id": row.account_id,
                    "customer_id": row.customer_id,
                    "account_type": row.account_type,
                    "status": row.status,
                    "current_balance": row.current_balance,
                }
                for row in rows
            ]
