from typing import Callable, List, Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    ForbiddenException,
    TokenInvalidException,
    UnauthorizedException,
    UserInactiveException,
)
from app.core.security import decode_jwt_token
from app.db.session import get_db_session
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token",
    auto_error=False,
)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Extracts, verifies, and resolves the current authenticated user from JWT Bearer token.
    Supports standard Bearer header and OpenAPI Swagger authorization.
    """
    token_str = token
    if not token_str and authorization and authorization.startswith("Bearer "):
        token_str = authorization.split(" ")[1]

    if not token_str:
        raise UnauthorizedException("Authentication token is missing.")

    payload = decode_jwt_token(token_str)

    if payload.get("type") != "access":
        raise TokenInvalidException("Access token required.")

    user_uuid = payload.get("sub")
    if not user_uuid:
        raise TokenInvalidException("Token subject missing.")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_uuid(user_uuid)
    if not user:
        raise UnauthorizedException("User not found.")

    if not user.is_active:
        raise UserInactiveException()

    return user


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    """
    Dependency factory enforcing Role-Based Access Control (RBAC).
    Usage: Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN))
    """

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException(
                f"Role '{current_user.role.value}' does not have sufficient permission for this endpoint."
            )
        return current_user

    return role_checker
