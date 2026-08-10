from typing import Generic, TypeVar

from pydantic import BaseModel

from sql_model.database.base import BaseTable
from sql_model.uow.sql import SQLUnitOfWork

T = TypeVar("T", bound=BaseTable)


class CRUDService(Generic[T]):
    def __init__(
        self,
        model: type[T],
        uow: SQLUnitOfWork,
    ) -> None:
        self.model = model
        self.uow = uow

    async def create(self, request: BaseModel) -> T:
        async with self.uow:
            entity = self.model(**request.model_dump())

            repository = self.uow.repository(self.model)
            entity = await repository.create(entity)

            await self.uow.commit()

            return entity
