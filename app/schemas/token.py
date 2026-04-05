from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: int  # expiry timestamp
    type: str  # "access" or "refresh"


class RefreshTokenCreate(BaseModel):
    user_id: str
    token_hash: str
    expires_at: datetime


class RefreshTokenOut(BaseModel):
    id: str
    user_id: str
    expires_at: datetime
    revoked: bool

    class Config:
        from_attributes = True
