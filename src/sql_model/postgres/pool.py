from typing import Any
import asyncpg

from sql_model.exceptions import DatabaseConnectionError


async def create_postgres_pool(
    database_url: str, min_size: int = 5, max_size: int = 20, **kwargs: Any
) -> asyncpg.Pool:
    """Create a high-performance asyncpg connection pool.

    Converts SQLModel/SQLAlchemy asyncpg URLs to standard postgresql URLs if necessary.
    """
    url = database_url
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    try:
        pool = await asyncpg.create_pool(
            dsn=url, min_size=min_size, max_size=max_size, **kwargs
        )
        if pool is None:
            raise DatabaseConnectionError("Failed to initialize asyncpg pool.")
        return pool
    except Exception as e:
        raise DatabaseConnectionError(f"Failed to create asyncpg pool: {e}") from e
