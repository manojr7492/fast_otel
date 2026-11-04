import math
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException
from app.core.telemetry import get_tracer
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedData, PaginationMeta, PaginationParams
from app.schemas.user import (
    UserDetailResponse,
    UserResponse,
    UserRoleUpdateRequest,
    UserStatusUpdateRequest,
    UserUpdateRequest,
)

tracer = get_tracer("user_service")


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def get_by_uuid(self, uuid_str: str) -> User:
        with tracer.start_as_current_span("user.get_by_uuid") as span:
            span.set_attribute("user.uuid", uuid_str)
            user = await self.user_repo.get_by_uuid(uuid_str)
            if not user:
                raise EntityNotFoundException("User", uuid_str)
            return user

    async def get_profile_with_addresses(self, uuid_str: str) -> UserDetailResponse:
        with tracer.start_as_current_span("user.get_profile_with_addresses") as span:
            span.set_attribute("user.uuid", uuid_str)
            user = await self.user_repo.get_with_addresses(uuid_str)
            if not user:
                raise EntityNotFoundException("User", uuid_str)
            span.set_attribute("user.address_count", len(user.addresses))
            return UserDetailResponse.model_validate(user)

    async def update_profile(
        self, user: User, update_in: UserUpdateRequest
    ) -> UserResponse:
        with tracer.start_as_current_span("user.update_profile") as span:
            span.set_attribute("user.uuid", user.uuid)
            update_data = update_in.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(user, key, value)

            await self.user_repo.update(user)
            await self.session.commit()
            await self.session.refresh(user)
            return UserResponse.model_validate(user)

    async def list_users(
        self,
        pagination: PaginationParams,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
    ) -> PaginatedData[UserResponse]:
        with tracer.start_as_current_span("user.list_users") as span:
            span.set_attribute("pagination.page", pagination.page)
            span.set_attribute("pagination.size", pagination.size)
            if role:
                span.set_attribute("filter.role", role.value)
            if is_active is not None:
                span.set_attribute("filter.is_active", is_active)

            items, total = await self.user_repo.list_users(
                offset=pagination.offset,
                limit=pagination.size,
                role=role,
                is_active=is_active,
            )

            total_pages = math.ceil(total / pagination.size) if total > 0 else 1
            user_responses = [UserResponse.model_validate(item) for item in items]
            span.set_attribute("result.total_records", total)

            meta = PaginationMeta(
                total_records=total,
                current_page=pagination.page,
                page_size=pagination.size,
                total_pages=total_pages,
                has_next=pagination.page < total_pages,
                has_prev=pagination.page > 1,
            )

            return PaginatedData(items=user_responses, pagination=meta)

    async def update_user_role(
        self, target_uuid: str, role_in: UserRoleUpdateRequest
    ) -> UserResponse:
        with tracer.start_as_current_span("user.update_role") as span:
            span.set_attribute("user.uuid", target_uuid)
            span.set_attribute("user.new_role", role_in.role.value)
            user = await self.get_by_uuid(target_uuid)
            user.role = role_in.role
            await self.user_repo.update(user)
            await self.session.commit()
            await self.session.refresh(user)
            return UserResponse.model_validate(user)

    async def update_user_status(
        self, target_uuid: str, status_in: UserStatusUpdateRequest
    ) -> UserResponse:
        with tracer.start_as_current_span("user.update_status") as span:
            span.set_attribute("user.uuid", target_uuid)
            span.set_attribute("user.is_active", status_in.is_active)
            user = await self.get_by_uuid(target_uuid)
            user.is_active = status_in.is_active
            await self.user_repo.update(user)
            await self.session.commit()
            await self.session.refresh(user)
            return UserResponse.model_validate(user)
