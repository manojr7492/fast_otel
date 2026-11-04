from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.services.payment_service import PaymentService


async def get_payment_service(
    session: AsyncSession = Depends(get_db_session),
) -> PaymentService:
    return PaymentService(session)

