"""Declarative base and model imports."""

from sqlalchemy.orm import DeclarativeBase

from app.db.database import engine  # noqa: F401  (re-exported convenience)


class Base(DeclarativeBase):
    pass


def create_all() -> None:
    """Create all tables.

    For the hackathon MVP we rely on metadata creation plus the seed script.
    A production deployment would manage schema via Alembic migrations.
    """
    from app import models  # noqa: F401  ensure models are registered

    Base.metadata.create_all(bind=engine)
