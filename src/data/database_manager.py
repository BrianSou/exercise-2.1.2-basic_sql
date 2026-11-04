"""SQLAlchemy engine and transaction management.

Use one engine per database and a fresh Session for each operation.
"""

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "original.db"


class DatabaseManager:
    def __init__(self, db_path=DEFAULT_DB, *, url=None, engine: Engine | None = None):
        if engine is not None:
            self.engine = engine
            self._owns_engine = False
        else:
            database_url = url or f"sqlite:///{Path(db_path).resolve().as_posix()}"
            self.engine = create_engine(database_url, pool_pre_ping=True)
            self._owns_engine = True
            if self.engine.dialect.name == "sqlite":
                @event.listens_for(self.engine, "connect")
                def set_sqlite_foreign_keys(connection, record):
                    cursor = connection.cursor()
                    try:
                        cursor.execute("PRAGMA foreign_keys=ON")
                    finally:
                        cursor.close()

        self._make_session = sessionmaker(bind=self.engine, expire_on_commit=False)

    @contextmanager
    def session(self):
        """Commit when successful; roll back and close when anything fails."""
        with self._make_session() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    def dispose(self):
        if self._owns_engine:
            self.engine.dispose()
