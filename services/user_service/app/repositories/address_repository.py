from typing import Optional, Sequence
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address
from app.repositories.base import BaseRepository


class AddressRepository(BaseRepository[Address]):
    def __init__(self, session: AsyncSession):
        super().__init__(Address, session)

    async def get_by_uuid_and_user_id(
        self, uuid_str: str, user_id: int
    ) -> Optional[Address]:
        result = await self.session.execute(
            select(Address).where(
                Address.uuid == uuid_str, Address.user_id == user_id
            )
        )
        return result.scalars().first()

    async def list_by_user_id(self, user_id: int) -> Sequence[Address]:
        result = await self.session.execute(
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(Address.is_default.desc(), Address.id.desc())
        )
        return result.scalars().all()

    async def reset_default_addresses(self, user_id: int) -> None:
        """Clear default flag on existing addresses for user prior to setting a new default."""
        await self.session.execute(
            update(Address)
            .where(Address.user_id == user_id, Address.is_default.is_(True))
            .values(is_default=False)
        )
