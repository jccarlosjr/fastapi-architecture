from typing import Generic, Sequence, TypeVar
from uuid import UUID

from pydantic import BaseModel

from app.core.generics.repository import GenericRepository

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class NotFoundError(Exception):
    """Levantada quando um recurso não existe. Mapeada para 404 globalmente."""


class GenericService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Camada de regra de negócio. Toda validação/orquestração que não é
    puramente persistência entra aqui, não no repository.
    """

    def __init__(self, repository: GenericRepository[ModelType]):
        self.repository = repository

    async def get(self, id: UUID) -> ModelType:
        obj = await self.repository.get(id)
        if obj is None:
            raise NotFoundError(f"{self.repository.model.__name__} {id} não encontrado")
        return obj

    async def list(self, *, offset: int = 0, limit: int = 100, **filters) -> Sequence[ModelType]:
        return await self.repository.list(offset=offset, limit=limit, **filters)

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        return await self.repository.create(obj_in.model_dump(exclude_unset=True))

    async def update(self, id: UUID, obj_in: UpdateSchemaType) -> ModelType:
        obj = await self.repository.update(id, obj_in.model_dump(exclude_unset=True))
        if obj is None:
            raise NotFoundError(f"{self.repository.model.__name__} {id} não encontrado")
        return obj

    async def delete(self, id: UUID) -> None:
        deleted = await self.repository.delete(id)
        if not deleted:
            raise NotFoundError(f"{self.repository.model.__name__} {id} não encontrado")
