import pytest
import pytest_asyncio
from typing import AsyncIterator
from sqlmodel import Field
from sqlalchemy.pool import NullPool

from sql_model import Database, BaseTable, temp_database, transaction_session


class TestItem(BaseTable, table=True):
    """Simple database model for unit/integration tests."""

    __test__ = False
    name: str = Field(nullable=False)
    description: str | None = Field(default=None, nullable=True)
    value: int = Field(default=0, nullable=False)


@pytest.fixture(scope="module")
def admin_db_url() -> str:
    """Return default admin URL for the local postgres instance."""
    return "postgresql+asyncpg://localhost:5432/postgres"


@pytest_asyncio.fixture
async def test_db_url(admin_db_url: str) -> AsyncIterator[str]:
    """Fixture to create a temporary test database and tear it down after test."""
    async with temp_database(admin_db_url) as url:
        yield url


@pytest_asyncio.fixture
async def test_engine(test_db_url: str):
    """Fixture that initializes the Database, connects, creates all tables, and yields engine."""
    db = Database(test_db_url, poolclass=NullPool)
    await db.connect()

    # Create tables
    async with db.engine.begin() as conn:
        await conn.run_sync(BaseTable.metadata.create_all)

    yield db.engine
    await db.disconnect()


@pytest_asyncio.fixture
async def session(test_engine) -> AsyncIterator:
    """Fixture to provide a transaction-isolated session for each test."""
    async with transaction_session(test_engine) as sess:
        yield sess
