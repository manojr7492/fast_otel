from typing import Optional, Sequence, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession):
        super().__init__(Product, session)

    async def get_by_sku(self, sku: str) -> Optional[Product]:
        res = await self.session.execute(select(Product).where(Product.sku == sku))
        return res.scalars().first()

    async def get_by_slug(self, slug: str) -> Optional[Product]:
        res = await self.session.execute(select(Product).where(Product.slug == slug))
        return res.scalars().first()

    async def list_products(
        self,
        offset: int = 0,
        limit: int = 20,
        category_id: Optional[int] = None,
        is_active: Optional[bool] = True,
        search_query: Optional[str] = None,
    ) -> Tuple[Sequence[Product], int]:
        stmt = select(Product)
        count_stmt = select(func.count()).select_from(Product)

        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
            count_stmt = count_stmt.where(Product.category_id == category_id)

        if is_active is not None:
            stmt = stmt.where(Product.is_active == is_active)
            count_stmt = count_stmt.where(Product.is_active == is_active)

        if search_query:
            term = f"%{search_query.strip()}%"
            stmt = stmt.where(Product.name.ilike(term) | Product.description.ilike(term))
            count_stmt = count_stmt.where(Product.name.ilike(term) | Product.description.ilike(term))

        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = stmt.order_by(Product.id.desc()).offset(offset).limit(limit)
        items_res = await self.session.execute(stmt)
        return items_res.scalars().all(), total

