"""Synchronous PostgreSQL sessions; no connection is opened during import."""
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


@lru_cache
def get_engine():
    try:
        url = make_url(settings.database_url)
        if url.drivername != "postgresql+psycopg":
            raise ValueError
    except (ValueError, ArgumentError):
        raise RuntimeError(
            "Set DATABASE_URL to a postgresql+psycopg URL in the project-root .env."
        ) from None
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 5})


@lru_cache
def get_session_factory():
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db():
    with get_session_factory()() as db:
        try:
            yield db
        except Exception:
            db.rollback()
            raise
