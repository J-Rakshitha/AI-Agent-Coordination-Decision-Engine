"""
Database engine + session management (async SQLAlchemy).
Works with SQLite in dev and Postgres in production by just
changing DATABASE_URL in .env — no code change needed.
"""
import asyncio
import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger("database")


class Base(DeclarativeBase):
    """Base class every ORM model inherits from."""
    pass


engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """FastAPI dependency that yields a DB session per request."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Create base tables, then apply Alembic migrations for additive schema changes."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        from app.core.migrations import run_migrations
        await asyncio.to_thread(run_migrations)
    except Exception as exc:
        logger.warning("Alembic migration step skipped or failed (non-fatal): %s", exc)
