import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings

_pools: dict[int, ConnectionPool] = {}


class LazyConnectionPool(ConnectionPool):
    def __init__(self) -> None:
        pass

    def __getattr__(self, name: str) -> Any:
        try:
            loop = asyncio.get_running_loop()
            loop_id = id(loop)
        except RuntimeError:
            loop_id = 0
        
        if loop_id not in _pools:
            _pools[loop_id] = ConnectionPool.from_url(
                settings.REDIS_URL, decode_responses=True, max_connections=50
            )
        return getattr(_pools[loop_id], name)


redis_pool = LazyConnectionPool()


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    FastAPI dependency that provides Redis client from the global connection pool
    """
    async with Redis(connection_pool=redis_pool) as client:
        yield client
