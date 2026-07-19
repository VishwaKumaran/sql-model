from typing import Any, Protocol, TypeVar
from sql_model.database.base import BaseTable
from sql_model.repositories.base import Repository

T = TypeVar("T", bound=BaseTable)


class UnitOfWork(Protocol):
    """Protocol defining the Unit of Work interface."""

    async def commit(self) -> None:
        """Commit the current transaction."""
        ...

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        ...

    def repository(self, model: type[T]) -> Repository[T]:
        """Get a repository bound to this Unit of Work's session."""
        ...

    async def __aenter__(self) -> "UnitOfWork": ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None: ...
