from app.core.exceptions import AppExceptionHandler
from app.core.generics.views import APIEndpoint
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.logging import setup_logging
from app.db.session import engine
from app.api.v1.routes import api_router
from app.core.config import settings
from app.core import middlewares

# Logging config initialization
setup_logging()

@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await engine.dispose()


# Application config initialization
app = FastAPI(
    title="Secure Auth & User Management API",
    description="FastAPI Minimal API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

AppExceptionHandler(app).register()

# Security middlewares
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)

app.add_middleware(middlewares.SecurityHeadersMiddleware)
app.add_middleware(middlewares.RateLimitMiddleware)
app.add_middleware(middlewares.RequestLogginMiddleware)

app.include_router(api_router, prefix="/api/v1")

class RootEndpoint(APIEndpoint):
    path = "/"
    method = "GET"

    async def handle(self) -> dict[str, str]:
        return {
            "message": "Welcome to FastAPI Minimal API. Go to /docs for Swagger documentation."
        }


RootEndpoint.register(app)

