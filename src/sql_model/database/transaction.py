from functools import wraps
from typing import Any, Callable, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession

F = TypeVar("F", bound=Callable[..., Any])


def transactional(method: F) -> F:
    """Decorator to run a method within an active transaction if a session is present in arguments.

    If the session is not already in a transaction, it begins one.
    """

    @wraps(method)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        session: AsyncSession | None = kwargs.get("session")
        if not session:
            for arg in args:
                if isinstance(arg, AsyncSession):
                    session = arg
                    break

        if session is not None:
            if not session.in_transaction():
                async with session.begin():
                    return await method(*args, **kwargs)
            else:
                return await method(*args, **kwargs)
        return await method(*args, **kwargs)

    return wrapper  # type: ignore
