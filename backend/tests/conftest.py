from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import get_db
from app.main import app as _app
from app.models import Base

TEST_DATABASE_URL = "sqlite:///./test_campaignpulse.db"
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
