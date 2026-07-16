import asyncio
from collections.abc import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTPX AsyncClient pointing to the FastAPI app."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
