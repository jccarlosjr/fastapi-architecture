from fastapi import APIRouter

from app.modules.accounts import routes as accounts_router
from app.modules.auth import routes as auth_router
from app.modules.groups import routes as groups_router
from app.modules.permissions import routes as permissions_router
from app.api.v1.health import HealthCheckEndpoint

api_router = APIRouter()
api_router.include_router(accounts_router.router, prefix="/accounts", tags=["Accounts"])
api_router.include_router(auth_router.router, prefix="/auth", tags=["Auth"])
api_router.include_router(groups_router.router, prefix="/groups", tags=["Groups"])
api_router.include_router(permissions_router.router, prefix="/permissions", tags=["Permissions"])

HealthCheckEndpoint.register(api_router)
