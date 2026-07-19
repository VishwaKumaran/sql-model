import base64
import json
from typing import Any, Generic, TypeVar
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Generic pagination response container."""

    items: list[T]
    total: int | None = None
    page: int | None = None
    size: int
    next_cursor: str | None = None
    previous_cursor: str | None = None


def encode_cursor(data: dict[str, Any]) -> str:
    """Encode dictionary data into a base64 string cursor."""
    json_bytes = json.dumps(data).encode("utf-8")
    return base64.urlsafe_b64encode(json_bytes).decode("utf-8")


def decode_cursor(cursor_str: str) -> dict[str, Any]:
    """Decode a base64 string cursor into a dictionary."""
    padding = "=" * (4 - len(cursor_str) % 4)
    decoded_bytes = base64.urlsafe_b64decode(cursor_str + padding)
    return json.loads(decoded_bytes.decode("utf-8"))


async def paginate_offset(
    session: AsyncSession, query: Any, page: int = 1, size: int = 20
) -> Page[Any]:
    """Perform offset-based pagination on an SQLAlchemy query."""
    if page < 1:
        page = 1
    if size < 1:
        size = 20

    # Count query
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar_one()

    # Paginated query
    paginated_query = query.offset((page - 1) * size).limit(size)
    result = await session.execute(paginated_query)
    items = list(result.scalars().all())

    return Page(items=items, total=total, page=page, size=size)


async def paginate_cursor(
    session: AsyncSession,
    query: Any,
    model: type,
    cursor: str | None = None,
    size: int = 20,
    sort_column: str = "id",
    descending: bool = False,
) -> Page[Any]:
    """Perform cursor-based pagination on an SQLAlchemy query.

    Assumes pagination is based on a unique/ordered field (like id or created_at).
    """
    if size < 1:
        size = 20

    col = getattr(model, sort_column)
    id_col = getattr(model, "id")

    # If cursor is provided, decode and apply filters
    if cursor:
        cursor_data = decode_cursor(cursor)
        cursor_val = cursor_data["value"]
        cursor_id = cursor_data["id"]

        if descending:
            query = query.where(
                (col < cursor_val) | ((col == cursor_val) & (id_col < cursor_id))
            )
        else:
            query = query.where(
                (col > cursor_val) | ((col == cursor_val) & (id_col > cursor_id))
            )

    # Sort
    if descending:
        query = query.order_by(col.desc(), id_col.desc())
    else:
        query = query.order_by(col.asc(), id_col.asc())

    # Limit to size + 1 to check if there is a next page
    query = query.limit(size + 1)
    result = await session.execute(query)
    items = list(result.scalars().all())

    has_more = len(items) > size
    if has_more:
        items = items[:size]

    next_cursor = None
    if has_more and items:
        last_item = items[-1]
        # Get raw value, serializing appropriately
        val = getattr(last_item, sort_column)
        if hasattr(val, "isoformat"):  # Handle datetime/date
            val = val.isoformat()
        elif hasattr(val, "hex"):  # Handle UUID
            val = val.hex

        next_cursor = encode_cursor({"value": val, "id": str(getattr(last_item, "id"))})

    return Page(items=items, size=size, next_cursor=next_cursor)
