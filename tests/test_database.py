import pytest
from sqlalchemy import text

from sql_model import Database, DatabaseConnectionError


@pytest.mark.asyncio
async def test_database_lifecycle(test_db_url: str):
    """Test connecting and disconnecting the database engine."""
    db = Database(test_db_url)

    # Test property access before connect
    with pytest.raises(DatabaseConnectionError):
        _ = db.engine

    with pytest.raises(DatabaseConnectionError):
        _ = db.session_factory

    # Connect
    await db.connect()
    assert db.engine is not None
    assert db.session_factory is not None

    # Test executing a simple query
    async with db.session() as session:
        res = await session.execute(text("SELECT 1"))
        assert res.scalar() == 1

    # Disconnect
    await db.disconnect()

    # Test property access after disconnect
    with pytest.raises(DatabaseConnectionError):
        _ = db.engine
