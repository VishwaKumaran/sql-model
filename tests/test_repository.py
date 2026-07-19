import pytest
import uuid

from sql_model import Repository, NotFoundError
from tests.conftest import TestItem


@pytest.mark.asyncio
async def test_repository_crud(session):
    """Test standard CRUD operations of the Repository."""
    repo = Repository(TestItem, session)

    # 1. Create
    item = TestItem(name="item1", description="desc1", value=10)
    created = await repo.create(item)
    assert created.id is not None
    assert created.name == "item1"
    assert created.created_at is not None
    assert created.updated_at is not None

    # 2. Get
    fetched = await repo.get(created.id)
    assert fetched is not None
    assert fetched.name == "item1"
    assert fetched.description == "desc1"

    # Get non-existing
    non_existing = await repo.get(uuid.uuid4())
    assert non_existing is None

    # 3. Update
    fetched.name = "updated_name"
    fetched.value = 20
    updated = await repo.update(fetched)
    assert updated.name == "updated_name"
    assert updated.value == 20

    # Verify in DB
    refetched = await repo.get(created.id)
    assert refetched.name == "updated_name"

    # 4. List with filter
    items = await repo.list(value=20)
    assert len(items) == 1
    assert items[0].id == created.id

    items_empty = await repo.list(value=999)
    assert len(items_empty) == 0

    # 5. Delete
    await repo.delete(created.id)

    # Confirm deletion
    deleted = await repo.get(created.id)
    assert deleted is None

    # Deleting non-existing should raise NotFoundError
    with pytest.raises(NotFoundError):
        await repo.delete(created.id)


@pytest.mark.asyncio
async def test_repository_pagination(session):
    """Test offset and cursor pagination in Repository."""
    repo = Repository(TestItem, session)

    # Create 5 items
    for i in range(5):
        await repo.create(TestItem(name=f"item_{i}", value=100 + i))

    # Offset pagination
    page1 = await repo.paginate_offset(page=1, size=2)
    assert len(page1.items) == 2
    assert page1.total == 5
    assert page1.page == 1
    assert page1.size == 2

    page2 = await repo.paginate_offset(page=2, size=2)
    assert len(page2.items) == 2
    assert page2.page == 2

    page3 = await repo.paginate_offset(page=3, size=2)
    assert len(page3.items) == 1

    # Cursor pagination
    cursor_page1 = await repo.paginate_cursor(size=2, sort_column="value")
    assert len(cursor_page1.items) == 2
    assert cursor_page1.next_cursor is not None
    assert cursor_page1.items[0].value == 100
    assert cursor_page1.items[1].value == 101

    # Get next page using cursor
    cursor_page2 = await repo.paginate_cursor(
        cursor=cursor_page1.next_cursor, size=2, sort_column="value"
    )
    assert len(cursor_page2.items) == 2
    assert cursor_page2.items[0].value == 102
    assert cursor_page2.items[1].value == 103
    assert cursor_page2.next_cursor is not None

    # Get final page
    cursor_page3 = await repo.paginate_cursor(
        cursor=cursor_page2.next_cursor, size=2, sort_column="value"
    )
    assert len(cursor_page3.items) == 1
    assert cursor_page3.items[0].value == 104
    assert cursor_page3.next_cursor is None
