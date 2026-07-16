from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.redis import get_redis
from app.api.v1.dependencies import get_client_ip
from app.core.security import decode_access_token
from app.core.middlewares import LoginRateLimiter
from app.core.config import settings
from app.core.mixins import LoginRequiredMixin
from app.core.generics.views import APIEndpoint, CreateAPIEndpoint

from .schemas import TokenResponse, LoginRequest, TokenRefreshRequest
from app.modules.auth import services

from app.modules.accounts.models import User
from app.modules.accounts.dependencies import get_current_user, oauth2_scheme


router = APIRouter()
logger = structlog.get_logger("app.auth")


class Login(CreateAPIEndpoint):
    """Authenticate the user and generate a JWT access token and an opaque refresh token.
    Includes network block by ip and email on redis (progressive backoff)."""
    path = "/login"
    response_model = TokenResponse

    db: AsyncSession = Depends(get_db)
    redis: Any = Depends(get_redis)

    async def handle(self, request: Request, login_in: LoginRequest) -> Any:
        ip = get_client_ip(request)
        await LoginRateLimiter.check_limit(self.redis, ip, login_in.email)

        try:
            user = await services.authenticate(self.db, login_in)
        except Exception as e:
            await LoginRateLimiter.register_failure(self.redis, ip, login_in.email)
            raise e

        # Reset failed attempts upon successful authentication
        await LoginRateLimiter.reset(self.redis, ip, login_in.email)

        refresh_token = await services.create_session(self.redis, str(user.id))
        access_token = services.create_access_token(subject=str(user.id), role=user.role)
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )


class Refresh(CreateAPIEndpoint):
    """Rotates the fresh token into a new JWT access token."""
    path = "/refresh"
    response_model = TokenResponse

    db: AsyncSession = Depends(get_db)
    redis: Any = Depends(get_redis)

    async def handle(self, refresh_in: TokenRefreshRequest) -> Any:
        access_token, new_refresh_token = await services.rotate_session(
            self.db, self.redis, refresh_in.refresh_token
        )
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )


class Logout(LoginRequiredMixin, APIEndpoint):
    """Revokes the current user's refresh token and adds the JWT token to the blacklist."""
    method = "POST"
    path = "/logout"
    status_code = status.HTTP_204_NO_CONTENT

    token: str = Depends(oauth2_scheme)
    redis: Any = Depends(get_redis)

    async def handle(self, refresh_in: TokenRefreshRequest) -> None:
        try:
            payload = decode_access_token(self.token)
        except Exception as e:
            logger.warning("logout_token_decode_failed", error=str(e))
            payload = {}

        jti = payload.get("jti")
        exp = payload.get("exp")

        expires_in = 0
        if exp:
            expires_in = int(exp - datetime.now(UTC).timestamp())

        await services.revoke_session(
            redis=self.redis,
            refresh_token=refresh_in.refresh_token,
            access_token_jti=jti if jti else "",
            access_token_expires_in=expires_in,
        )


Login.register(router)
Refresh.register(router)
Logout.register(router)
