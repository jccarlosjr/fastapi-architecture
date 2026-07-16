from typing import Any
from fastapi import Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.db.session import get_db
from app.db.redis import get_redis
from app.core.generics.views import APIEndpoint


class HealthCheckEndpoint(APIEndpoint):
    path = "/health"
    method = "GET"
    status_code = status.HTTP_200_OK

    db: AsyncSession = Depends(get_db)
    redis: Any = Depends(get_redis)

    async def handle(self) -> JSONResponse:
        database_status = "down"
        redis_status = "down"
        errors = {}

        # 1. Test PostgreSQL
        try:
            await self.db.execute(text("SELECT 1"))
            database_status = "up"
        except Exception as e:
            errors["database"] = str(e)

        # 2. Test Redis
        try:
            await self.redis.ping()
            redis_status = "up"
        except Exception as e:
            errors["redis"] = str(e)

        is_healthy = database_status == "up" and redis_status == "up"
        payload = {
            "status": "healthy" if is_healthy else "unhealthy",
            "database": database_status,
            "redis": redis_status,
        }

        if not is_healthy:
            payload["details"] = errors
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=payload
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=payload
        )
