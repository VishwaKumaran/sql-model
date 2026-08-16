from typing import Any

from alembic import context
from sqlalchemy.ext.asyncio import AsyncEngine


def run_migrations_offline(target_metadata: Any) -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL and the target metadata.
    """
    url = context.get_x_argument(as_dictionary=True).get(
        "url"
    ) or context.config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Any, target_metadata: Any) -> None:
    """Run migrations within a synchronous transaction context.

    Invoked from run_migrations_online on an AsyncEngine.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online(target_metadata: Any, engine: AsyncEngine) -> None:
    """Run migrations in 'online' mode using AsyncEngine.run_sync."""
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations, target_metadata)
