import pytest

from sql_model import create_postgres_pool, BulkWriter, Repository
from tests.conftest import TestItem


@pytest.mark.asyncio
async def test_bulk_writer(test_db_url: str, session):
    """Test direct high-performance bulk writes using asyncpg."""
    # 1. Create asyncpg pool
    pool = await create_postgres_pool(test_db_url)
    assert pool is not None

    try:
        writer = BulkWriter(pool)

        # Define bulk records (omitting id, created_at, updated_at to rely on server defaults)
        records = [{"name": f"bulk_item_{i}", "value": 1000 + i} for i in range(10)]

        # Execute insert_many
        # The table name is test_item (snake_case of TestItem)
        await writer.insert_many("test_item", records)

        # Verify via repository
        repo = Repository(TestItem, session)
        items = await repo.list()

        bulk_items = [item for item in items if item.name.startswith("bulk_item_")]
        assert len(bulk_items) == 10

        # Verify values
        for i, item in enumerate(sorted(bulk_items, key=lambda x: x.value)):
            assert item.name == f"bulk_item_{i}"
            assert item.value == 1000 + i
            assert item.id is not None
            assert item.created_at is not None
            assert item.updated_at is not None

    finally:
        await pool.close()
