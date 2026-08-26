"""SQLAlchemy engine and session management."""

import logging
from collections.abc import Generator
from urllib.parse import urlsplit

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger("Unnati")

IS_SQLITE = settings.DATABASE_URL.startswith("sqlite")


def _ensure_mysql_database(url: str) -> None:
    """MySQL cannot auto-create a database on connect — create it once at startup.

    Uses utf8mb4 so chat messages (emoji) and farmer names store correctly.
    """
    parts = urlsplit(url)
    if parts.scheme.split("+")[0] != "mysql" or not parts.path.lstrip("/"):
        return
    dbname = parts.path.lstrip("/").split("?")[0]
    admin_url = f"{parts.scheme}://{parts.netloc}/?charset=utf8mb4"
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text(
                    "SELECT 1 FROM information_schema.schemata WHERE schema_name = :name"
                ),
                {"name": dbname},
            ).scalar()
            if not exists:
                conn.execute(
                    text(
                        f"CREATE DATABASE `{dbname}` "
                        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                    )
                )
                logger.info("Created MySQL database '%s'.", dbname)
    finally:
        admin_engine.dispose()


if not IS_SQLITE:
    try:
        _ensure_mysql_database(settings.DATABASE_URL)
    except Exception:  # noqa: BLE001 - app still starts; first query will surface it
        logger.exception("Could not provision the MySQL database automatically.")


_engine_kwargs: dict = {
    "connect_args": {"check_same_thread": False} if IS_SQLITE else {},
    "future": True,
}
if not IS_SQLITE:
    # Survive idle disconnects ("MySQL server has gone away").
    _engine_kwargs.update(pool_pre_ping=True, pool_recycle=3600)

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
