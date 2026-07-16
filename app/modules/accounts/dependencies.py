import uuid
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token

from app.db.redis import get_redis
from app.db.session import get_db
from app.modules.accounts.models import User
from app.modules.accounts.repositories import UserRepository
from app.modules.accounts.services import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))



async def get_current_user(
    db: AsyncSession = Depends(get_db),
    redis: Any = Depends(get_redis),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Retrieve a valid the JWT claims from auth header.
    Verify if token is on the blacklist.
    Return the authenticated user or throws 401 Unauthorized.
    """
    # Exception raised when the token is invalid or expired
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Token or Credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode access token
    try:
        payload = decode_access_token(token)
    except Exception as e:
        raise credentials_exception from e

    # Verify if the token is in the redis blacklist
    jti = payload.get("jti")
    if jti:
        is_blacklisted = await redis.get(f"blacklist:{jti}")
        if is_blacklisted:
            raise credentials_exception

    subject: str | None = payload.get("sub")
    if not subject:
        raise credentials_exception

    # Verify if the user has revoked all sessions
    revoke_ts = await redis.get(f"user_revoke_all:{subject}")
    if revoke_ts:
        # If the token iat is less than the revoke timestamp, it means the token is invalid
        if payload.get("iat", 0) < float(revoke_ts):
            raise credentials_exception

    try: 
        user_id = uuid.UUID(subject)
    except ValueError:
        raise credentials_exception from None

    # Verify if the user is active
    user = await UserRepository(db).get_by_id_with_permissions(user_id)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not active"
        )

    return user