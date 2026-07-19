from contextlib import asynccontextmanager
import uuid
from typing import AsyncIterator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)


@asynccontextmanager
async def temp_database(admin_db_url: str) -> AsyncIterator[str]:
    """Async context manager to create a temporary database and drop it afterwards.

    Args:
        admin_db_url: URL to the admin database (e.g., 'postgresql+asyncpg://postgres:postgres@localhost:5432/postgres')
    """
    db_name = f"test_db_{uuid.uuid4().hex[:8]}"

    # Ensure driver is asyncpg for admin engine
    url = admin_db_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    # 1. Connect to admin DB and create database
    admin_engine = create_async_engine(url, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        await conn.execute(text(f"CREATE DATABASE {db_name}"))
    await admin_engine.dispose()

    # Reconstruct url
    base, _ = url.rsplit("/", 1)
    db_url = f"{base}/{db_name}"

    try:
        yield db_url
    finally:
        # Terminate connections and drop database
        admin_engine = create_async_engine(url, isolation_level="AUTOCOMMIT")
        async with admin_engine.connect() as conn:
            await conn.execute(
                text(
                    f"SELECT pg_terminate_backend(pid) "
                    f"FROM pg_stat_activity "
                    f"WHERE datname = '{db_name}' "
                    f"AND pid <> pg_backend_pid()"
                )
            )
            await conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
        await admin_engine.dispose()


@asynccontextmanager
async def transaction_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Provide an AsyncSession that is automatically rolled back on completion.

    Perfect for running individual tests in transactional isolation.
    """
    connection = await engine.connect()
    transaction = await connection.begin()

    session_factory = async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()
            await connection.close()
