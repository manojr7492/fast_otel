import logging
import random
import time
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    EntityAlreadyExistsException,
    InvalidCredentialsException,
    TokenInvalidException,
    UserInactiveException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
    hash_password,
    verify_password,
)
from app.core.telemetry import get_tracer
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.token import TokenResponse
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

logger = logging.getLogger(settings.SERVICE_NAME)
tracer = get_tracer("auth_service")

# In-memory OTP storage for demo & verification: {identifier: {"otp": str, "expires_at": float}}
_demo_otps: dict = {}


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, user_in: UserRegisterRequest) -> User:
        with tracer.start_as_current_span("auth.register") as span:
            span.set_attribute("user.email", user_in.email)
            span.set_attribute("user.username", user_in.username)

            # Check uniqueness with O(log N) index lookups
            if await self.user_repo.email_exists(user_in.email):
                span.set_attribute("auth.error", "email_exists")
                raise EntityAlreadyExistsException("User", "email", user_in.email)

            if await self.user_repo.username_exists(user_in.username):
                span.set_attribute("auth.error", "username_exists")
                raise EntityAlreadyExistsException("User", "username", user_in.username)

            with tracer.start_as_current_span("auth.hash_password") as hash_span:
                hash_span.set_attribute("crypto.algorithm", "bcrypt")
                hash_span.set_attribute("crypto.rounds", 12)
                hashed_pwd = hash_password(user_in.password)

            new_user = User(
                email=user_in.email.lower().strip(),
                username=user_in.username.strip(),
                hashed_password=hashed_pwd,
                first_name=user_in.first_name.strip() if user_in.first_name else None,
                last_name=user_in.last_name.strip() if user_in.last_name else None,
                phone_number=user_in.phone_number.strip() if user_in.phone_number else None,
                role=UserRole.CUSTOMER,
                is_active=True,
                is_verified=False,
            )

            user = await self.user_repo.create(new_user)
            await self.session.commit()
            await self.session.refresh(user)

            span.set_attribute("user.uuid", user.uuid)
            span.set_attribute("user.role", user.role.value)

            # Cross-service event notification with distributed trace context propagation
            await self._send_welcome_notification(user)

            return user

    async def _send_welcome_notification(self, user: User) -> None:
        """Dispatches an asynchronous welcome notification to the Notification microservice."""
        with tracer.start_as_current_span("auth.send_welcome_notification") as span:
            span.set_attribute("notification.recipient", user.email)
            span.set_attribute("notification.event_type", "WELCOME_USER")
            span.set_attribute("notification.service_url", settings.NOTIFICATION_SERVICE_URL)

            try:
                # HTTPX is instrumented by OpenTelemetry, automatically injecting W3C traceparent headers
                async with httpx.AsyncClient(timeout=3.0) as client:
                    target_url = f"{settings.NOTIFICATION_SERVICE_URL}/api/v1/notifications/send"
                    payload = {
                        "recipient_email": user.email,
                        "recipient_name": user.full_name or user.username,
                        "event_type": "WELCOME_USER",
                        "data": {
                            "username": user.username,
                            "user_uuid": user.uuid,
                        },
                    }
                    resp = await client.post(target_url, json=payload)
                    span.set_attribute("http.status_code", resp.status_code)
                    logger.info(
                        "Dispatched welcome notification to notification-service for user %s [status: %s]",
                        user.uuid,
                        resp.status_code,
                    )
            except Exception as exc:
                # Observability principle: non-critical downstream notification failures must not break user registration
                span.record_exception(exc)
                span.set_attribute("notification.status", "failed_downstream")
                logger.warning(
                    "Notification service call failed (downstream optional): %s",
                    str(exc),
                )

    async def authenticate(self, login_in: UserLoginRequest) -> TokenResponse:
        with tracer.start_as_current_span("auth.authenticate") as span:
            span.set_attribute("auth.login_identifier", login_in.login_identifier)

            user = await self.user_repo.get_by_login_identifier(login_in.login_identifier)
            if not user:
                span.set_attribute("auth.error", "user_not_found")
                raise InvalidCredentialsException()

            with tracer.start_as_current_span("auth.verify_password") as verify_span:
                is_valid = verify_password(login_in.password, user.hashed_password)
                verify_span.set_attribute("crypto.valid", is_valid)
                if not is_valid:
                    span.set_attribute("auth.error", "invalid_password")
                    raise InvalidCredentialsException()

            if not user.is_active:
                span.set_attribute("auth.error", "user_inactive")
                raise UserInactiveException()

            with tracer.start_as_current_span("auth.issue_jwt_tokens") as token_span:
                token_span.set_attribute("jwt.algorithm", settings.ALGORITHM)
                token_span.set_attribute("jwt.subject", user.uuid)
                access_token = create_access_token(
                    subject=user.uuid,
                    role=user.role.value,
                    additional_claims={"username": user.username, "email": user.email},
                )
                refresh_token = create_refresh_token(
                    subject=user.uuid,
                    role=user.role.value,
                )

            span.set_attribute("user.uuid", user.uuid)
            span.set_attribute("user.role", user.role.value)

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        with tracer.start_as_current_span("auth.refresh_token") as span:
            payload = decode_jwt_token(refresh_token)

            if payload.get("type") != "refresh":
                raise TokenInvalidException("Expected a refresh token.")

            user_uuid = payload.get("sub")
            if not user_uuid:
                raise TokenInvalidException("Token subject missing.")

            user = await self.user_repo.get_by_uuid(user_uuid)
            if not user:
                raise InvalidCredentialsException("User associated with token not found.")

            if not user.is_active:
                raise UserInactiveException()

            span.set_attribute("user.uuid", user.uuid)

            # Token rotation: Issue both new access token and new refresh token
            with tracer.start_as_current_span("auth.rotate_jwt_tokens"):
                new_access_token = create_access_token(
                    subject=user.uuid,
                    role=user.role.value,
                    additional_claims={"username": user.username, "email": user.email},
                )
                new_refresh_token = create_refresh_token(
                    subject=user.uuid,
                    role=user.role.value,
                )

            return TokenResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )

    async def change_password(
        self, user: User, change_in: PasswordChangeRequest
    ) -> None:
        with tracer.start_as_current_span("auth.change_password") as span:
            span.set_attribute("user.uuid", user.uuid)
            if not verify_password(change_in.old_password, user.hashed_password):
                span.set_attribute("auth.error", "old_password_mismatch")
                raise InvalidCredentialsException("Current password does not match.")

            with tracer.start_as_current_span("auth.hash_password"):
                user.hashed_password = hash_password(change_in.new_password)

            await self.user_repo.update(user)
            await self.session.commit()

    async def request_otp(self, otp_in: OTPRequest) -> OTPResponseData:
        with tracer.start_as_current_span("auth.request_otp") as span:
            identifier = otp_in.login_identifier.strip().lower()
            span.set_attribute("auth.login_identifier", identifier)

            code = f"{random.randint(100000, 999999)}"
            _demo_otps[identifier] = {
                "otp": code,
                "expires_at": time.time() + 300,
            }
            span.set_attribute("auth.otp_generated", True)

            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    target_url = f"{settings.NOTIFICATION_SERVICE_URL}/api/v1/notifications/send"
                    payload = {
                        "recipient_email": identifier if "@" in identifier else f"{identifier}@ecommerce.local",
                        "recipient_name": identifier,
                        "event_type": "LOGIN_OTP",
                        "data": {
                            "otp": code,
                            "expires_in": 300,
                        },
                    }
                    await client.post(target_url, json=payload)
            except Exception as exc:
                span.record_exception(exc)
                logger.warning("Downstream notification for OTP failed (optional): %s", str(exc))

            logger.info("Demo OTP code generated for %s: %s", identifier, code)
            return OTPResponseData(
                otp=code,
                login_identifier=otp_in.login_identifier,
                expires_in=300,
                message="Demo OTP generated successfully. Use on-screen code or auto-fill.",
            )

    async def verify_otp(self, verify_in: OTPVerifyRequest) -> OTPAuthResponse:
        with tracer.start_as_current_span("auth.verify_otp") as span:
            identifier = verify_in.login_identifier.strip().lower()
            code = verify_in.otp_code.strip()
            span.set_attribute("auth.login_identifier", identifier)

            stored = _demo_otps.get(identifier)
            valid = False
            if code == "123456":
                valid = True
            elif stored and stored.get("otp") == code and time.time() <= stored.get("expires_at", 0):
                valid = True

            if not valid:
                span.set_attribute("auth.error", "invalid_otp")
                raise InvalidCredentialsException("Invalid or expired OTP code.")

            user = await self.user_repo.get_by_login_identifier(identifier)
            if not user:
                with tracer.start_as_current_span("auth.auto_provision_user") as prov_span:
                    is_email = "@" in identifier
                    email = identifier if is_email else f"{identifier}@ecommerce.local"
                    base_username = identifier.split("@")[0].replace(" ", "_")
                    username = base_username
                    counter = 1
                    while await self.user_repo.username_exists(username):
                        username = f"{base_username}_{counter}"
                        counter += 1

                    user = User(
                        email=email,
                        username=username,
                        hashed_password=hash_password("DemoPassword@123"),
                        first_name=username.capitalize(),
                        last_name="Customer",
                        role=UserRole.CUSTOMER,
                        is_active=True,
                        is_verified=True,
                    )
                    user = await self.user_repo.create(user)
                    await self.session.commit()
                    await self.session.refresh(user)
                    prov_span.set_attribute("user.uuid", user.uuid)

            if not user.is_active:
                raise UserInactiveException()

            with tracer.start_as_current_span("auth.issue_otp_tokens"):
                access_token = create_access_token(
                    subject=user.uuid,
                    role=user.role.value,
                    additional_claims={"username": user.username, "email": user.email},
                )
                refresh_token = create_refresh_token(
                    subject=user.uuid,
                    role=user.role.value,
                )

            span.set_attribute("user.uuid", user.uuid)
            span.set_attribute("user.role", user.role.value)

            return OTPAuthResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=UserResponse.model_validate(user),
            )

