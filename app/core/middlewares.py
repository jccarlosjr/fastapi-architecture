import time
import uuid
from typing import Any
import structlog

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from redis.asyncio import Redis

from app.db.redis import redis_pool
from app.core.config import settings
from app.core.exceptions import RateLimitExceeded

logger = structlog.get_logger("middleware.request")


class RequestLogginMiddleware(BaseHTTPMiddleware):
    """
    Middleware to inject X-Request-ID in each request and register
    metrics of latency, origin IP, HTTP status and route
    """
    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] == "websocket":
            await self.app(scope, receive, send)
            return
        await super().__call__(scope, receive, send)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        start_time = time.time()
        response = await call_next(request)
        proccess_time = time.time() - start_time

        response.headers["X-Request-ID"] = request_id

        from app.api.v1.dependencies import get_client_ip

        ip = get_client_ip(request)

        logger.info(
            "http_request",
            ip=ip,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration=f"{proccess_time:.4f}s",
            request_id=request_id
        )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to inject recommended security headers HTTP (OWASP/Helmet equivalent)
    """
    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] == "websocket":
            await self.app(scope, receive, send)
            return
        await super().__call__(scope, receive, send)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "img-src 'self' data: cdn.jsdelivr.net;"
        )
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


_RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local current = redis.call('INCR', key)
if current == 1 then
    redis.call('EXPIRE', key, window)
end
return current  
"""

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate Limiting Global Middleware based on the client IP.
    Limit requests based on the configuration set in the application.
    """

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] == "websocket":
            await self.app(scope, receive, send)
            return
        await super().__call__(scope, receive, send)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        from app.api.v1.dependencies import get_client_ip

        ip = get_client_ip(request)
        key = f"rate_limit:ip:{ip}"

        async with Redis(connection_pool=redis_pool) as redis:
            from collections.abc import Coroutine
            from typing import cast

            current = await cast(
                Coroutine[Any, Any, Any],
                redis.eval(
                    _RATE_LIMIT_SCRIPT,
                    1,
                    key,
                    str(settings.RATE_LIMIT_GLOBAL_MAX_REQUESTS),
                    str(settings.RATE_LIMIT_GLOBAL_WINDOW_SECONDS)
                ),
            )
            if int(current) > settings.RATE_LIMIT_GLOBAL_MAX_REQUESTS:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": (
                            "Too many requests. Please try again later."
                        )
                    }
                )

        return await call_next(request)


class LoginRateLimiter:
    """
    Utility class for managing login rate limits and locks.
    """

    @classmethod
    async def check_limit(cls, redis: Redis, ip: str, email: str) -> None:
        """
        Check if IP or e-mail are temporarily blocked
        due to too many failed login attempts.
        """
        ip_lock = await redis.get(f"login_lock:ip:{ip}")
        email_lock = await redis.get(f"login_lock:email:{email.strip().lower()}")

        if ip_lock or email_lock:
            raise RateLimitExceeded(
                "Too many failed login attempts. Your account/IP has been temporarily blocked."
            )

    @classmethod
    async def register_failure(cls, redis: Redis, ip: str, email: str) -> None:
        """
        Register a failed login attempt for both IP and e-mail and apply a progressive backoff.
        """
        email_clean = email.strip().lower()
        ip_key = f"login_lock:ip:{ip}"
        email_key = f"login_lock:email:{email_clean}"

        attempts_ip = await redis.incr(ip_key)
        if attempts_ip == 1:
            await redis.expire(ip_key, 900)  # 15 minutes

        attempts_email = await redis.incr(email_key)
        if attempts_email == 1:
            await redis.expire(email_key, 900)  # 15 minutes

        max_attempts = max(attempts_ip, attempts_email)

        if max_attempts >= settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS:
            if max_attempts == 5:
                lock_time = 60  # 1 minute
            elif max_attempts == 6:
                lock_time = 300  # 5 minutes
            elif max_attempts == 7:
                lock_time = 900  # 15 minutes
            else:
                lock_time = 3600  # 1 hour

            await redis.set(f"login_lock:ip:{ip}", "locked", ex=lock_time)
            await redis.set(f"login_lock:email:{email_clean}", "locked", ex=lock_time)

            logger.warning(
                "login_rate_limit",
                ip=ip,
                email=email_clean,
                attempts=max_attempts,
                lock_time=lock_time,
            )

    @classmethod
    async def reset(cls, redis: Redis, ip: str, email: str) -> None:
        """
        Reset all counter and remove locks on Redis after login success.
        """
        email_clean = email.strip().lower()
        await redis.delete(
            f"login_attempts:ip:{ip}",
            f"login_attempts:email:{email_clean}",
            f"login_lock:ip:{ip}",
            f"login_lock:email:{email_clean}",
        )
