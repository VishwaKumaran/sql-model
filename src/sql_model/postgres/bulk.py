from typing import Any, Sequence
import asyncpg

from sql_model.exceptions import BulkWriteError


class BulkWriter:
    """High-performance bulk writer using direct asyncpg COPY operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def insert_many(
        self, table_name: str, records: Sequence[dict[str, Any]]
    ) -> None:
        """Insert a large volume of records into a table using postgres COPY.

        All records must have the exact same keys/columns.
        """
        if not records:
            return

        columns = list(records[0].keys())
        data = [tuple(r.get(col) for col in columns) for r in records]

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    await conn.copy_records_to_table(
                        table_name, records=data, columns=columns
                    )
        except Exception as e:
            raise BulkWriteError(f"Failed to bulk insert into {table_name}: {e}") from e
