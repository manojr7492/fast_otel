from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, require_roles
from app.core.exceptions import ForbiddenException
from app.models.user import User, UserRole
from app.schemas.common import APIResponse, PaginatedData, PaginationParams
from app.schemas.user import (
    UserDetailResponse,
    UserResponse,
    UserRoleUpdateRequest,
    UserStatusUpdateRequest,
    UserUpdateRequest,
)
from app.services.user_service import UserService

router = APIRouter()


@router.get(
    "/me",
    response_model=APIResponse[UserDetailResponse],
    summary="Get current authenticated user profile with addresses",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = UserService(db)
    profile = await service.get_profile_with_addresses(current_user.uuid)
    return APIResponse(
        message="Profile retrieved successfully.",
        data=profile,
    )


@router.patch(
    "/me",
    response_model=APIResponse[UserResponse],
    summary="Update current authenticated user details",
)
async def update_my_profile(
    update_in: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = UserService(db)
    updated = await service.update_profile(current_user, update_in)
    return APIResponse(
        message="Profile updated successfully.",
        data=updated,
    )


@router.get(
    "/",
    response_model=APIResponse[PaginatedData[UserResponse]],
    summary="List users with pagination and filtering (Admin only)",
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by status"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
):
    service = UserService(db)
    pagination = PaginationParams(page=page, size=size)
    paginated_users = await service.list_users(
        pagination=pagination, role=role, is_active=is_active
    )
    return APIResponse(
        message="Users retrieved successfully.",
        data=paginated_users,
    )


@router.get(
    "/{uuid}",
    response_model=APIResponse[UserDetailResponse],
    summary="Get user by UUID (Admin or account owner)",
)
async def get_user_by_uuid(
    uuid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    if current_user.uuid != uuid and current_user.role not in [
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ]:
        raise ForbiddenException("You can only view your own user account.")

    service = UserService(db)
    user_detail = await service.get_profile_with_addresses(uuid)
    return APIResponse(
        message="User details retrieved successfully.",
        data=user_detail,
    )


@router.patch(
    "/{uuid}/role",
    response_model=APIResponse[UserResponse],
    summary="Update user role (Super Admin & Admin only)",
)
async def update_user_role(
    uuid: str,
    role_in: UserRoleUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
):
    service = UserService(db)
    updated = await service.update_user_role(uuid, role_in)
    return APIResponse(
        message="User role updated successfully.",
        data=updated,
    )


@router.patch(
    "/{uuid}/status",
    response_model=APIResponse[UserResponse],
    summary="Activate or deactivate a user account (Admin only)",
)
async def update_user_status(
    uuid: str,
    status_in: UserStatusUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db_session),
):
    service = UserService(db)
    updated = await service.update_user_status(uuid, status_in)
    return APIResponse(
        message="User status updated successfully.",
        data=updated,
    )
