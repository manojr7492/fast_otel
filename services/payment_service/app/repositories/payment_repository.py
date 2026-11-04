from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import PaymentTransaction
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[PaymentTransaction]):
    def __init__(self, session: AsyncSession):
        super().__init__(PaymentTransaction, session)

    async def get_by_order_uuid(self, order_uuid: str) -> Optional[PaymentTransaction]:
        res = await self.session.execute(
            select(PaymentTransaction)
            .where(PaymentTransaction.order_uuid == order_uuid)
            .order_by(PaymentTransaction.id.desc())
        )
        return res.scalars().first()

    async def get_by_reference(self, reference: str) -> Optional[PaymentTransaction]:
        res = await self.session.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.transaction_reference == reference
            )
        )
        return res.scalars().first()

