from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# ═══════════════════════════════════════════════════════════════════════
# IMPORTANT: Set the test DB URL *before* importing app modules so the
# app-level engine uses the test database, not production.  This prevents
# the lifespan handler (Base.metadata.create_all + seed_demo_data) from
# touching the production database.
# ═══════════════════════════════════════════════════════════════════════
TEST_DATABASE_URL = "sqlite:///./test_campaignpulse.db"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# ── Ensure test DB is cleaned up after all tests ──────────────────
@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_db() -> Generator[None, None, None]:
    yield
    db_path = TEST_DATABASE_URL.replace("sqlite:///./", "")
    if os.path.exists(db_path):
        os.remove(db_path)
import app.main as _app_mod  # noqa: E402
from app.database import get_db  # noqa: E402
from app.models import Base  # noqa: E402

_app = _app_mod.app


def _noop_seed() -> None:
    """Swap in a no-op seed so the lifespan doesn't pollute test DB."""


_app_mod.seed_demo_data = _noop_seed

_test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
_test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def override_get_db() -> Generator[Session, None, None]:
    """Override the database dependency for tests."""
    db = _test_session_local()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database() -> Generator[None, None, None]:
    """Create tables before each test and drop them after."""
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def app() -> FastAPI:
    """Return the FastAPI app with overridden dependencies."""
    _app.dependency_overrides[get_db] = override_get_db
    return _app


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Return a test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Return a database session for test setup."""
    db = _test_session_local()
    try:
        yield db
    finally:
        db.close()
