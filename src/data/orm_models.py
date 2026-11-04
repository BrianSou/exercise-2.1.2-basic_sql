"""SQLAlchemy mappings for the original Week 2 complaint database.

These classes describe database tables. Business validation belongs in
src.domain.models, not here.
"""

from decimal import Decimal
from sqlalchemy import ForeignKey, Numeric, String, Text, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CustomerRow(Base):
    __tablename__ = "customer"

    customer_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str | None] = mapped_column(String(120))


class AccountRow(Base):
    __tablename__ = "account"

    account_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customer.customer_id"), nullable=False)
    account_type: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[str | None] = mapped_column(String(20))
    current_balance: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))


class ComplaintRow(Base):
    __tablename__ = "complaint"

    complaint_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customer.customer_id"), nullable=False)
    account_id: Mapped[str | None] = mapped_column(ForeignKey("account.account_id"))
    channel: Mapped[str | None] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    complaint_text: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    # Week 2 stores received_at as text in SQLite. Keep the mapping compatible.
    received_at: Mapped[str] = mapped_column(String(40), nullable=False)
    assigned_analyst_id: Mapped[str | None] = mapped_column(String(10))


class ComplaintStatusEventRow(Base):
    __tablename__ = "complaint_status_history"

    history_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    complaint_id: Mapped[str] = mapped_column(ForeignKey("complaint.complaint_id"), nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(20))
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by: Mapped[str] = mapped_column(String(10), nullable=False)
    changed_at: Mapped[str] = mapped_column(String(40), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text)
