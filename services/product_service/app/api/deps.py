from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.services.product_service import ProductCatalogService


async def get_catalog_service(
    session: AsyncSession = Depends(get_db_session),
) -> ProductCatalogService:
    return ProductCatalogService(session)

