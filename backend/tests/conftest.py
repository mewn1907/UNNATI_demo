"""Shared pytest fixtures: isolated database + API client."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Isolate from any developer .env before importing app modules.
os.environ.setdefault("LLM_ENABLED", "false")
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("WEATHER_ENABLED", "false")

_tmpdir = tempfile.mkdtemp(prefix="Unnati-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmpdir).as_posix()}/test.db"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import create_all  # noqa: E402
from app.db.seed import seed  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _seed_database() -> None:
    create_all()
    seed()


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session():
    from app.db.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
