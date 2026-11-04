"""3.2.1 checks FastAPI and SQLAlchemy readiness without PostgreSQL."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool
from src.api.main import create_app
from src.config import Settings
from src.dependencies import (
    check_database, get_readiness_checker, get_db_session, get_engine,
)

DB_ENV = {
    "DB_HOST": "localhost", "DB_PORT": "5432",
    "DB_NAME": "complaints_training", "DB_USER": "training_user",
    "DB_PASSWORD": "a@b:/secret",
}


@pytest.fixture
def no_env(monkeypatch):
    for key in DB_ENV:
        monkeypatch.delenv(key, raising=False)
    get_engine.cache_clear()


@pytest.fixture
def db_env(monkeypatch):
    for key, value in DB_ENV.items():
        monkeypatch.setenv(key, value)
    get_engine.cache_clear()


def test_liveness_without_database(no_env):
    with TestClient(create_app()) as client:
        assert client.get("/health/live").json() == {"status": "ok"}


def test_readiness_without_configuration(no_env):
    with TestClient(create_app()) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["code"] == "DEPENDENCY_UNAVAILABLE"


def test_readiness_rejects_bad_port(db_env, monkeypatch):
    monkeypatch.setenv("DB_PORT", "bad")
    with TestClient(create_app()) as client:
        assert client.get("/health/ready").status_code == 503


@pytest.mark.parametrize("port", ["x", "0", "65536"])
def test_settings_reject_invalid_port(db_env, monkeypatch, port):
    monkeypatch.setenv("DB_PORT", port)
    with pytest.raises(ValueError, match="DB_PORT"):
        Settings.from_environment()


def test_settings_make_safe_postgresql_url(db_env):
    settings = Settings.from_environment()
    url = settings.database_url()
    assert isinstance(url, URL)
    assert url.drivername == "postgresql+psycopg"
    assert url.password == DB_ENV["DB_PASSWORD"]
    assert DB_ENV["DB_PASSWORD"] not in repr(settings)
    assert DB_ENV["DB_PASSWORD"] not in str(url)


def test_injected_ready():
    app = create_app()
    app.dependency_overrides[get_readiness_checker] = lambda: (lambda: True)
    with TestClient(app) as client:
        assert client.get("/health/ready").json() == {"status": "ready"}


def test_injected_not_ready():
    app = create_app()
    app.dependency_overrides[get_readiness_checker] = lambda: (lambda: False)
    with TestClient(app) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503


def test_injected_exception_is_sanitized():
    app = create_app()
    def fail():
        raise RuntimeError("secret_password_should_not_be_returned")
    app.dependency_overrides[get_readiness_checker] = lambda: fail
    with TestClient(app) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert "secret_password_should_not_be_returned" not in response.text


def test_ready_uses_sqlalchemy_connection_and_select_one():
    engine = create_engine("sqlite+pysqlite:///:memory:", poolclass=QueuePool)
    queries = []
    @event.listens_for(engine, "before_cursor_execute")
    def record(connection, cursor, statement, parameters, context, many):
        queries.append(statement)
    try:
        assert check_database(engine=engine) is True
        assert queries == ["SELECT 1"]
        assert engine.pool.checkedout() == 0  # connection was returned to pool
    finally:
        engine.dispose()


def test_failed_database_query_is_not_ready():
    class BrokenEngine:
        def connect(self):
            raise RuntimeError("secret connection details")
    assert check_database(engine=BrokenEngine()) is False


def test_db_session_yields_real_sqlalchemy_session(monkeypatch):
    from src import dependencies
    engine = create_engine("sqlite+pysqlite:///:memory:")
    monkeypatch.setattr(dependencies, "get_engine", lambda: engine)
    factory = get_db_session()
    try:
        session = next(factory)
        assert isinstance(session, Session)
    finally:
        factory.close()
        engine.dispose()


def test_openapi_and_docs():
    with TestClient(create_app()) as client:
        doc = client.get("/openapi.json")
        assert doc.status_code == 200
        assert client.get("/docs").status_code == 200
        paths = doc.json()["paths"]
        assert "/health/live" in paths
        assert "/health/ready" in paths


def test_routers_exist_but_need_database_configuration(no_env):
    with TestClient(create_app()) as client:
        assert client.get("/customers/CUS001").status_code == 503
        assert client.get("/complaints/CMP001").status_code == 503


def test_api_does_not_require_credentials_at_startup(no_env):
    # The app can start without any connection; only readiness requires DB access.
    with TestClient(create_app()) as client:
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 503


def test_get_engine_builds_postgresql_sqlalchemy_engine(db_env, monkeypatch):
    from src import dependencies
    calls = []
    marker = object()
    def fake_create_engine(url, **kwargs):
        calls.append((url, kwargs))
        return marker
    monkeypatch.setattr(dependencies, "create_engine", fake_create_engine)
    dependencies.get_engine.cache_clear()
    try:
        assert dependencies.get_engine() is marker
        assert dependencies.get_engine() is marker  # engine reused
        assert len(calls) == 1
        assert calls[0][0].drivername == "postgresql+psycopg"
        assert calls[0][1]["connect_args"]["connect_timeout"] == 3
        assert calls[0][1]["pool_pre_ping"] is True
    finally:
        dependencies.get_engine.cache_clear()
