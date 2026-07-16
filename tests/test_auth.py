import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient) -> None:
    """Test that the RootEndpoint returns the correct welcome message."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "Welcome to FastAPI Minimal API" in response.json()["message"]


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient) -> None:
    """Test that the HealthCheckEndpoint is functioning."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "up"
    assert data["redis"] == "up"


@pytest.mark.asyncio
async def test_me_endpoint_requires_auth(client: AsyncClient) -> None:
    """Test that the /me endpoint requires login and blocks unauthenticated requests."""
    response = await client.get("/api/v1/accounts/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient) -> None:
    """Test login with invalid credentials returns 401/400."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "wrongpassword123"}
    )
    assert response.status_code in (400, 401, 429)
