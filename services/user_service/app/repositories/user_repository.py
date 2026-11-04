from typing import Optional, Sequence, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username.strip())
        )
        return result.scalars().first()

    async def get_by_login_identifier(self, identifier: str) -> Optional[User]:
        clean_identifier = identifier.strip()
        result = await self.session.execute(
            select(User).where(
                or_(
                    User.email == clean_identifier.lower(),
                    User.username == clean_identifier,
                )
            )
        )
        return result.scalars().first()

    async def get_with_addresses(self, uuid_str: str) -> Optional[User]:
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.addresses))
            .where(User.uuid == uuid_str)
        )
        return result.scalars().first()

    async def email_exists(self, email: str) -> bool:
        result = await self.session.execute(
            select(func.count(User.id)).where(User.email == email.lower().strip())
        )
        return (result.scalar_one() or 0) > 0

    async def username_exists(self, username: str) -> bool:
        result = await self.session.execute(
            select(func.count(User.id)).where(User.username == username.strip())
        )
        return (result.scalar_one() or 0) > 0

    async def list_users(
        self,
        offset: int = 0,
        limit: int = 20,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[Sequence[User], int]:
        query = select(User)
        count_query = select(func.count(User.id))

        if role is not None:
            query = query.where(User.role == role)
            count_query = count_query.where(User.role == role)

        if is_active is not None:
            query = query.where(User.is_active == is_active)
            count_query = count_query.where(User.is_active == is_active)

        total_res = await self.session.execute(count_query)
        total = total_res.scalar_one()

        paginated_res = await self.session.execute(
            query.order_by(User.id.desc()).offset(offset).limit(limit)
        )
        items = paginated_res.scalars().all()

        return items, total
