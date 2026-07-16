from typing import Any, Generic, Sequence, Type, TypeVar
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class GenericRepository(Generic[ModelType]):
    """
    Repository genérico: só lida com persistência, nada de regra de negócio.
    Subclasse define `model` e pode adicionar queries específicas.
    """
    model: Type[ModelType]
    auto_commit: bool = True

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: UUID) -> ModelType | None:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def list(
        self, *, offset: int = 0, limit: int = 100, **filters: Any
    ) -> Sequence[ModelType]:
        stmt = select(self.model).offset(offset).limit(limit)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        obj = self.model(**obj_in)
        self.session.add(obj)
        if self.auto_commit:
            await self.session.commit()
        else:
            await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, id: UUID, obj_in: dict[str, Any]) -> ModelType | None:
        if not obj_in:
            return await self.get(id)
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**obj_in)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        if self.auto_commit:
            await self.session.commit()
        else:
            await self.session.flush()
        return obj

    async def delete(self, id: UUID) -> bool:
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        deleted = result.rowcount > 0
        if self.auto_commit:
            await self.session.commit()
        else:
            await self.session.flush()
        return deleted
