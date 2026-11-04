from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.services.inventory_service import InventoryService


async def get_inventory_service(
    session: AsyncSession = Depends(get_db_session),
) -> InventoryService:
    return InventoryService(session)

