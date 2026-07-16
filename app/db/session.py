from contextlib import AbstractAsyncContextManager
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from contextvars import ContextVar

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)

from app.core.config import settings

# Async engine from SQLAlchemy setting with suited pool conections
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Async Session with context var and async context manager
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Context var for holding active session
session_context: ContextVar[AsyncSession | None] = ContextVar(
    "session_context", default=None
)

@asynccontextmanager
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager that provides an active session.
    If has a session in ContextVar, uses it without closing.
    Otherwise, open a new session in the pool and close it at the end.
    """
    context_session = session_context.get()
    if context_session is not None:
        yield context_session
    else:
        async with AsyncSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI - returns an async session and ensures it is closed.
    """
    async with db_session() as session:
        yield session
