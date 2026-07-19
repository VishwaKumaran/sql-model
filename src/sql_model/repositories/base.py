import uuid
from typing import Any, Generic, TypeVar
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from sql_model.database.base import BaseTable
from sql_model.exceptions import ConflictError, NotFoundError, RepositoryError
from sql_model.repositories.pagination import (
    Page,
    paginate_cursor,
    paginate_offset,
)

T = TypeVar("T", bound=BaseTable)


class Repository(Generic[T]):
    """Generic async repository providing standard CRUD operations for SQLModel models."""

    def __init__(self, model: type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: uuid.UUID) -> T | None:
        """Retrieve an entity by its UUID."""
        try:
            return await self.session.get(self.model, id)
        except Exception as e:
            raise RepositoryError(
                f"Error retrieving {self.model.__name__} (id: {id}): {e}"
            ) from e

    async def list(self, **filters: Any) -> list[T]:
        """List entities matching simple filters."""
        try:
            query = select(self.model)
            for key, val in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == val)
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            raise RepositoryError(f"Error listing {self.model.__name__}: {e}") from e

    async def create(self, entity: T) -> T:
        """Create a new entity in the database."""
        try:
            self.session.add(entity)
            await self.session.flush()
            await self.session.refresh(entity)
            return entity
        except IntegrityError as e:
            await self.session.rollback()
            raise ConflictError(f"Conflict creating {self.model.__name__}: {e}") from e
        except Exception as e:
            await self.session.rollback()
            raise RepositoryError(f"Error creating {self.model.__name__}: {e}") from e

    async def add(self, entity: T) -> T:
        """Alias for create, aligning with standard Unit of Work interfaces."""
        return await self.create(entity)

    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        try:
            self.session.add(entity)
            await self.session.flush()
            await self.session.refresh(entity)
            return entity
        except IntegrityError as e:
            await self.session.rollback()
            raise ConflictError(f"Conflict updating {self.model.__name__}: {e}") from e
        except Exception as e:
            await self.session.rollback()
            raise RepositoryError(f"Error updating {self.model.__name__}: {e}") from e

    async def delete(self, id: uuid.UUID) -> None:
        """Delete an entity by its UUID."""
        try:
            entity = await self.get(id)
            if not entity:
                raise NotFoundError(f"{self.model.__name__} with ID {id} not found.")
            await self.session.delete(entity)
            await self.session.flush()
        except NotFoundError:
            raise
        except IntegrityError as e:
            await self.session.rollback()
            raise ConflictError(f"Conflict deleting {self.model.__name__}: {e}") from e
        except Exception as e:
            await self.session.rollback()
            raise RepositoryError(f"Error deleting {self.model.__name__}: {e}") from e

    async def paginate_offset(
        self, page: int = 1, size: int = 20, **filters: Any
    ) -> Page[T]:
        """Get a page of entities using offset pagination."""
        try:
            query = select(self.model)
            for key, val in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == val)
            return await paginate_offset(self.session, query, page, size)
        except Exception as e:
            raise RepositoryError(f"Error paginating {self.model.__name__}: {e}") from e

    async def paginate_cursor(
        self,
        cursor: str | None = None,
        size: int = 20,
        sort_column: str = "id",
        descending: bool = False,
        **filters: Any,
    ) -> Page[T]:
        """Get a page of entities using cursor pagination."""
        try:
            query = select(self.model)
            for key, val in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == val)
            return await paginate_cursor(
                self.session,
                query,
                self.model,
                cursor=cursor,
                size=size,
                sort_column=sort_column,
                descending=descending,
            )
        except Exception as e:
            raise RepositoryError(
                f"Error cursor-paginating {self.model.__name__}: {e}"
            ) from e
