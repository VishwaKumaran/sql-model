import logging
from typing import Any, AsyncIterator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
    AsyncSession,
)
from contextlib import asynccontextmanager

from sql_model.exceptions import DatabaseConnectionError
from sql_model.database.session import manage_session

logger = logging.getLogger(__name__)


class Database:
    """PostgreSQL Database abstraction using SQLAlchemy AsyncEngine and connection pooling."""

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: float = 30.0,
        pool_recycle: int = 1800,
        pool_pre_ping: bool = True,
        **kwargs: Any,
    ):
        url = database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)

        self.database_url = url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.pool_pre_ping = pool_pre_ping
        self.extra_kwargs = kwargs
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def connect(self) -> None:
        """Initialize the AsyncEngine and sessionmaker with connection pooling."""
        if self._engine is not None:
            return

        try:
            kwargs = self.extra_kwargs.copy()
            poolclass = kwargs.get("poolclass")

            if poolclass is not None and poolclass.__name__ == "NullPool":
                self._engine = create_async_engine(self.database_url, **kwargs)
            else:
                self._engine = create_async_engine(
                    self.database_url,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_timeout=self.pool_timeout,
                    pool_recycle=self.pool_recycle,
                    pool_pre_ping=self.pool_pre_ping,
                    **kwargs,
                )
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                expire_on_commit=False,
                class_=AsyncSession,
            )
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e

    async def disconnect(self) -> None:
        """Dispose of the AsyncEngine and close all pooled connections."""
        if self._engine is None:
            return

        try:
            await self._engine.dispose()
        except Exception as e:
            logger.warning(f"Error during database engine disposal: {e}")
        finally:
            self._engine = None
            self._session_factory = None

    @property
    def engine(self) -> AsyncEngine:
        """Get the AsyncEngine instance."""
        if self._engine is None:
            raise DatabaseConnectionError(
                "Database is not connected. Call connect() first."
            )
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get the session factory instance."""
        if self._session_factory is None:
            raise DatabaseConnectionError(
                "Database is not connected. Call connect() first."
            )
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Provide an async session context manager with automatic transaction lifecycle management."""
        if self._session_factory is None:
            raise DatabaseConnectionError(
                "Database is not connected. Call connect() first."
            )

        async with manage_session(self._session_factory) as sess:
            yield sess
