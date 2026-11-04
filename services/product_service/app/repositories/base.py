from typing import Generic, Optional, Sequence, Type, TypeVar
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalars().first()

    async def get_by_uuid(self, uuid_str: str) -> Optional[ModelType]:
        result = await self.session.execute(
            select(self.model).where(self.model.uuid == uuid_str)
        )
        return result.scalars().first()

    async def list_paginated(
        self, offset: int = 0, limit: int = 20
    ) -> Sequence[ModelType]:
        result = await self.session.execute(
            select(self.model)
            .order_by(self.model.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def count(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar() or 0

    async def create(self, instance: ModelType) -> ModelType:
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, instance: ModelType) -> ModelType:
        await self.session.flush()
        return instance

    async def delete(self, instance: ModelType) -> None:
        await self.session.delete(instance)
        await self.session.flush()

