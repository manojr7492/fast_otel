from typing import Optional, Sequence, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderStatus
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    def __init__(self, session: AsyncSession):
        super().__init__(Order, session)

    async def get_with_items(self, uuid_str: str) -> Optional[Order]:
        res = await self.session.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.uuid == uuid_str)
        )
        return res.scalars().first()

    async def list_orders(
        self,
        offset: int = 0,
        limit: int = 20,
        user_uuid: Optional[str] = None,
        status: Optional[OrderStatus] = None,
    ) -> Tuple[Sequence[Order], int]:
        stmt = select(Order).options(selectinload(Order.items))
        count_stmt = select(func.count()).select_from(Order)

        if user_uuid:
            stmt = stmt.where(Order.user_uuid == user_uuid)
            count_stmt = count_stmt.where(Order.user_uuid == user_uuid)

        if status:
            stmt = stmt.where(Order.status == status)
            count_stmt = count_stmt.where(Order.status == status)

        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = stmt.order_by(Order.id.desc()).offset(offset).limit(limit)
        items_res = await self.session.execute(stmt)
        return items_res.scalars().all(), total

