from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, session: AsyncSession):
        super().__init__(Category, session)

    async def get_by_slug(self, slug: str) -> Optional[Category]:
        res = await self.session.execute(select(Category).where(Category.slug == slug))
        return res.scalars().first()

    async def get_by_name(self, name: str) -> Optional[Category]:
        res = await self.session.execute(select(Category).where(Category.name == name))
        return res.scalars().first()

    async def list_all(self) -> Sequence[Category]:
        res = await self.session.execute(select(Category).order_by(Category.name.asc()))
        return res.scalars().all()

