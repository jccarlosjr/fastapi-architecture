
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import status

from app.modules.accounts.repositories import UserRepository
from app.modules.accounts.models import User
from app.core.exceptions import AuthenticationError, DomainException
from app.core import security
from app.core.config import settings
from app.core.security import create_access_token

from .schemas import LoginRequest


async def authenticate(db: AsyncSession, login_in: LoginRequest) -> User:
    """
    Authenticate a user by email and password.
    Temporarily blocks users after failed attempts.
    """
    repo = UserRepository(db)
    user = await repo.get_by_email(login_in.email)

    if not user:
        raise AuthenticationError("Invalid credentials")
    
    if not user.is_active:
        raise DomainException(
            "User account is not active. Please contact the administrator.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    if user.locked_until and user.locked_until > datetime.now(UTC):
        raise DomainException(
            "Too many failed login attempts. Account locked. Please contact support.",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    
    if not security.verify_password(login_in.password, user.hashed_password):
        failed_count = user.failed_login_count + 1
        locked_until = None

        if failed_count >= settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS:
            locked_until = datetime.now(UTC) + timedelta(
                seconds=settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS
            )
            failed_count = 0
        
        await repo.update_user(
            user, {"failed_login_count": failed_count, "locked_until": locked_until}
        )
        raise AuthenticationError("Invalid credentials")

    if user.failed_login_count > 0 or user.locked_until:
        await repo.update_user(
            user, {"failed_login_count": 0, "locked_until": None}
        )

    return user


async def create_session(redis: Any, user_id: str) -> str:
    """
    Create a new session in redis for the user and generate a opaque refresh token
    """
    jti = str(uuid.uuid4())
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

    token_key = f"refresh:{jti}"
    sessions_key = f"user_sessions:{user_id}"

    await redis.set(token_key, user_id, ex=ttl)
    await redis.sadd(sessions_key, jti)
    await redis.expire(sessions_key, ttl)
    return jti


async def revoke_all_sessions(redis: Any, user_id: str) -> None:
    """
    Revoke all sessions for a user
    """
    sessions_key = f"user_sessions:{user_id}"
    active_jtis = await redis.smembers(sessions_key)
    if active_jtis:
        keys_to_delete = [f"refresh:{jti}" for jti in active_jtis]
        await redis.delete(*keys_to_delete)
    await redis.delete(sessions_key)

    revoke_key = f"user_revoke_all:{user_id}"
    timestamp = str(datetime.now(UTC).timestamp())
    await redis.set(revoke_key, timestamp, ex=86400)


async def rotate_session(
    db: AsyncSession, redis: Any, refresh_token: str
) -> tuple[str, str]:
    """
    Rotate a refresh token to prevent replay attacks. 
    Revokes all sessions for a user.
    """
    token_key = f"refresh:{refresh_token}"
    user_id = await redis.get(token_key)

    if not user_id:
        # Token not found. Verify if it was previously used. (Replay attack)
        used_key = f"used_refresh:{refresh_token}"
        previous_user_id = await redis.get(used_key)
        if previous_user_id:
            # Replay attack detected. Revoke all sessions for the previous user.
            await revoke_all_sessions(redis, previous_user_id)
            raise AuthenticationError("Invalid or expired credentials. All sessions revoked.")
        raise AuthenticationError("Invalid or expired credentials.")

    user = await UserRepository(db).get(uuid.UUID(user_id))
    if not user or not user.is_active:
        raise AuthenticationError("Invalid or inactive user.")
    
    sessions_key = f"user_sessions:{user_id}"
    await redis.delete(token_key)
    await redis.srem(sessions_key, refresh_token)
    await redis.set(
        f"used_refresh:{refresh_token}", user_id, ex=300
    ) # 5 minutes for replay audit

    new_jti = await create_session(redis, user_id)
    new_access_token = create_access_token(subject=str(user.id), role=user.role)
    return new_access_token, new_jti


async def revoke_session(
    redis: Any, refresh_token: str, access_token_jti: str, access_token_expires_in: int
) -> None:
    token_key = f"refresh:{refresh_token}"
    user_id = await redis.get(token_key)

    if user_id:
        sessions_key = f"user_sessions:{user_id}"
        await redis.srem(sessions_key, refresh_token)
        await redis.delete(token_key)
    
    if access_token_expires_in > 0:
        blacklist_key = f"blacklist:{access_token_jti}"
        await redis.set(blacklist_key, "revoked", ex=access_token_expires_in)
