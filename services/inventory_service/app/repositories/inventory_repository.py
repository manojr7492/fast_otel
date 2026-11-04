from typing import List, Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem, StockReservation
from app.repositories.base import BaseRepository


class InventoryRepository(BaseRepository[InventoryItem]):
    def __init__(self, session: AsyncSession):
        super().__init__(InventoryItem, session)

    async def get_by_sku(self, sku: str) -> Optional[InventoryItem]:
        res = await self.session.execute(
            select(InventoryItem).where(InventoryItem.sku == sku)
        )
        return res.scalars().first()

    async def get_reservations_by_order(self, order_uuid: str) -> Sequence[StockReservation]:
        res = await self.session.execute(
            select(StockReservation).where(
                StockReservation.order_uuid == order_uuid,
                StockReservation.status == "ACTIVE",
            )
        )
        return res.scalars().all()

    async def create_reservation(self, order_uuid: str, sku: str, quantity: int) -> StockReservation:
        res = StockReservation(
            order_uuid=order_uuid,
            sku=sku,
            quantity=quantity,
            status="ACTIVE",
        )
        self.session.add(res)
        await self.session.flush()
        return res

