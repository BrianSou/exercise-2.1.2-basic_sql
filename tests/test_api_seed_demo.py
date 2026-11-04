"""Check that optional demo setup is safe and uses the ORM table structure."""

from sqlalchemy import create_engine, select, func
import pytest

from src.api.seed_demo import seed_demo
from src.data.orm_models import CustomerRow, AccountRow, ComplaintRow, ComplaintStatusEventRow


def test_demo_seed_and_no_repeat(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'api_demo.db'}")
    try:
        counts = seed_demo(engine)
        assert counts == {"customers": 10, "accounts": 10,
                          "complaints": 30, "history_events": 30}
        with engine.connect() as connection:
            assert connection.scalar(select(func.count()).select_from(CustomerRow)) == 10
            assert connection.scalar(select(func.count()).select_from(AccountRow)) == 10
            assert connection.scalar(select(func.count()).select_from(ComplaintRow)) == 30
            assert connection.scalar(select(func.count()).select_from(ComplaintStatusEventRow)) == 30
        with pytest.raises(ValueError, match="contain data"):
            seed_demo(engine)
        with engine.connect() as connection:
            assert connection.scalar(select(func.count()).select_from(ComplaintRow)) == 30
    finally:
        engine.dispose()
