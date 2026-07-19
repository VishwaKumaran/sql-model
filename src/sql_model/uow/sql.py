from typing import Any, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from sql_model.database.base import BaseTable
from sql_model.exceptions import TransactionError
from sql_model.repositories.base import Repository
from sql_model.uow.protocol import UnitOfWork

T = TypeVar("T", bound=BaseTable)


class SQLUnitOfWork(UnitOfWork):
    """SQLAlchemy implementation of the Unit of Work pattern."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self.session: AsyncSession | None = None
        self._repositories: dict[type, Repository] = {}

    async def __aenter__(self) -> "SQLUnitOfWork":
        if self.session is not None:
            raise TransactionError("Unit of Work is already active in this context.")

        self.session = self.session_factory()
        # Start transaction
        await self.session.begin()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if self.session is None:
            return

        try:
            if exc_type is not None:
                await self.rollback()
            elif self.session.in_transaction():
                # If exit is reached without exception but transaction is still active,
                # rollback to prevent uncommitted changes (safe-by-default).
                await self.rollback()
        finally:
            await self.session.close()
            self.session = None
            self._repositories.clear()

    async def commit(self) -> None:
        """Commit current transaction."""
        if self.session is None:
            raise TransactionError("No active session to commit.")
        try:
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise TransactionError(f"Failed to commit transaction: {e}") from e

    async def rollback(self) -> None:
        """Rollback current transaction."""
        if self.session is None:
            raise TransactionError("No active session to rollback.")
        try:
            await self.session.rollback()
        except Exception as e:
            raise TransactionError(f"Failed to rollback transaction: {e}") from e

    def repository(self, model: type[T]) -> Repository[T]:
        """Retrieve or create a generic repository bound to the current session."""
        if self.session is None:
            raise TransactionError(
                "Cannot access repository outside of an active Unit of Work."
            )
        if model not in self._repositories:
            self._repositories[model] = Repository(model, self.session)
        return self._repositories[model]
