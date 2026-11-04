import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
import jwt

from app.core.config import settings
from app.core.exceptions import TokenExpiredException, TokenInvalidException


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with a generated salt.
    Complexity: O(1) space, cost factor calibrated time.
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against an existing bcrypt hash.
    Constant-time comparison prevents timing attacks.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_token(
    subject: str,
    role: str,
    token_type: str,
    expires_delta: timedelta,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a signed JWT token containing subject, role, type, expiration, and unique JTI.
    """
    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()),
    }

    if additional_claims:
        payload.update(additional_claims)

    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_access_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_token(
        subject=subject,
        role=role,
        token_type="access",
        expires_delta=delta,
        additional_claims=additional_claims,
    )


def create_refresh_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_token(
        subject=subject,
        role=role,
        token_type="refresh",
        expires_delta=delta,
    )


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token signature and expiration.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub", "type"]},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredException("Token has expired")
    except jwt.InvalidTokenError as exc:
        raise TokenInvalidException(f"Invalid token: {str(exc)}")
