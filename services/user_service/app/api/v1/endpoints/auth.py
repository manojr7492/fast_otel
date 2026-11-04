from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.token import RefreshTokenRequest, TokenResponse
from app.schemas.user import (
    OTPAuthResponse,
    OTPRequest,
    OTPResponseData,
    OTPVerifyRequest,
    PasswordChangeRequest,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer account",
)
async def register(
    user_in: UserRegisterRequest,
    db: AsyncSession = Depends(get_db_session),
):
    service = AuthService(db)
    user = await service.register(user_in)
    return APIResponse(
        status_code=status.HTTP_201_CREATED,
        message="User account registered successfully.",
        data=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    summary="Authenticate user with email/username and password",
)
async def login(
    login_in: UserLoginRequest,
    db: AsyncSession = Depends(get_db_session),
):
    service = AuthService(db)
    tokens = await service.authenticate(login_in)
    return APIResponse(
        message="Authentication successful.",
        data=tokens,
    )


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="OAuth2 compatible token login for Swagger UI documentation",
)
async def oauth2_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
):
    service = AuthService(db)
    tokens = await service.authenticate(
        UserLoginRequest(
            login_identifier=form_data.username,
            password=form_data.password,
        )
    )
    return tokens


@router.post(
    "/refresh",
    response_model=APIResponse[TokenResponse],
    summary="Refresh access token using a valid refresh token",
)
async def refresh_token(
    refresh_in: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session),
):
    service = AuthService(db)
    tokens = await service.refresh_access_token(refresh_in.refresh_token)
    return APIResponse(
        message="Tokens refreshed successfully.",
        data=tokens,
    )


@router.post(
    "/change-password",
    response_model=APIResponse[dict],
    summary="Change account password for current user",
)
async def change_password(
    change_in: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = AuthService(db)
    await service.change_password(current_user, change_in)
    return APIResponse(
        message="Password updated successfully.",
        data={"updated": True},
    )


@router.post(
    "/otp/request",
    response_model=APIResponse[OTPResponseData],
    summary="Request a 6-digit OTP code for demo/instant login",
)
async def request_otp(
    payload: OTPRequest,
    db: AsyncSession = Depends(get_db_session),
):
    service = AuthService(db)
    data = await service.request_otp(payload)
    return APIResponse(
        message="OTP generated successfully. Check on-screen demo banner.",
        data=data,
    )


@router.post(
    "/otp/verify",
    response_model=APIResponse[OTPAuthResponse],
    summary="Verify 6-digit OTP code and establish user session",
)
async def verify_otp(
    payload: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db_session),
):
    service = AuthService(db)
    auth_data = await service.verify_otp(payload)
    return APIResponse(
        message="OTP verified successfully. Authenticated session established.",
        data=auth_data,
    )

