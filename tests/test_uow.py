import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from sql_model import SQLUnitOfWork, Repository
from tests.conftest import TestItem


@pytest.mark.asyncio
async def test_uow_commit(test_engine, session):
    """Test that Unit of Work commits changes successfully."""
    session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)

    # 1. Create and commit via UOW
    async with SQLUnitOfWork(session_factory) as uow:
        repo = uow.repository(TestItem)
        item = await repo.add(TestItem(name="uow_committed", value=1))
        item_id = item.id
        await uow.commit()

    # Verify item is committed and accessible
    repo_verify = Repository(TestItem, session)
    fetched = await repo_verify.get(item_id)
    assert fetched is not None
    assert fetched.name == "uow_committed"


@pytest.mark.asyncio
async def test_uow_rollback_on_error(test_engine, session):
    """Test that Unit of Work rolls back automatically when an exception is raised."""
    session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)
    item_id = None

    try:
        async with SQLUnitOfWork(session_factory) as uow:
            repo = uow.repository(TestItem)
            item = await repo.add(TestItem(name="uow_error", value=2))
            item_id = item.id
            # Raise exception to trigger rollback
            raise ValueError("Forced error")
    except ValueError:
        pass

    # Verify item was not committed
    repo_verify = Repository(TestItem, session)
    fetched = await repo_verify.get(item_id)
    assert fetched is None


@pytest.mark.asyncio
async def test_uow_rollback_implicit(test_engine, session):
    """Test that Unit of Work rolls back automatically if exit is reached without explicit commit."""
    session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)
    item_id = None

    async with SQLUnitOfWork(session_factory) as uow:
        repo = uow.repository(TestItem)
        item = await repo.add(TestItem(name="uow_implicit_rollback", value=3))
        item_id = item.id
        # Exit context without calling uow.commit()

    # Verify item was not committed
    repo_verify = Repository(TestItem, session)
    fetched = await repo_verify.get(item_id)
    assert fetched is None
