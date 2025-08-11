"""
Database configuration and session management.
"""

import contextlib
from typing import AsyncIterator

from sqlalchemy import MetaData, create_engine, event, Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from app.core.config import get_settings


# Database metadata with naming conventions for migrations
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

# Base class for all database models
Base = declarative_base(metadata=metadata)


class DatabaseSessionManager:
    """
    Database session manager for async operations.
    """

    def __init__(self):
        self._engine = None
        self._sessionmaker = None

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncSession]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                session = AsyncSession(bind=connection)
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    def init(self, host: str, **kwargs):
        """Initialize the database session manager."""
        settings = get_settings()

        engine_kwargs = {
            "echo": settings.DEBUG,
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_pre_ping": True,
            "pool_recycle": 300,  # 5 minutes
            **kwargs
        }

        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )


# Global session manager instance
sessionmanager = DatabaseSessionManager()

# Synchronous engine for Alembic migrations
def get_sync_engine():
    """Get synchronous engine for Alembic migrations."""
    settings = get_settings()
    return create_engine(
        settings.DATABASE_URL_SYNC,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )


# Synchronous session for Alembic
def get_sync_session() -> Session:
    """Get synchronous session for Alembic migrations."""
    engine = get_sync_engine()
    return Session(engine)


# Dependency to get database session
async def get_db() -> AsyncIterator[AsyncSession]:
    async with sessionmanager.session() as session:
        yield session


# Event listeners for database optimization
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance (if using SQLite)."""
    if 'sqlite' in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        # Optimize for speed
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=1000000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()