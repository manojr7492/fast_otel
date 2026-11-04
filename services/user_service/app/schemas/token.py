from typing import Optional
from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifespan in seconds")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid refresh token")


class TokenPayload(BaseModel):
    sub: str
    role: str
    type: str
    exp: int
    iat: Optional[int] = None
    jti: Optional[str] = None
