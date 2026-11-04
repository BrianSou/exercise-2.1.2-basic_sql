"""PostgreSQL settings are read from environment variables."""

import os
from dotenv import load_dotenv

# Load local settings, but never overwrite real environment variables.
load_dotenv()
from dataclasses import dataclass, field
from sqlalchemy.engine import URL


@dataclass(frozen=True)
class Settings:
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str = field(repr=False)

    @classmethod
    def from_environment(cls):
        names = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
        missing = [name for name in names if not os.getenv(name, "").strip()]
        if missing:
            raise ValueError("Missing database settings: " + ", ".join(missing))
        try:
            port = int(os.environ["DB_PORT"])
        except ValueError as exc:
            raise ValueError("DB_PORT must be a number") from exc
        if not 1 <= port <= 65535:
            raise ValueError("DB_PORT must be between 1 and 65535")
        return cls(
            db_host=os.environ["DB_HOST"].strip(),
            db_port=port,
            db_name=os.environ["DB_NAME"].strip(),
            db_user=os.environ["DB_USER"].strip(),
            db_password=os.environ["DB_PASSWORD"],
        )

    def database_url(self):
        """URL.create handles passwords containing @, : or / safely."""
        return URL.create(
            "postgresql+psycopg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )
