from typing import Any
from fastapi import APIRouter, Depends

from app.core.security import hash_password
from app.core.mixins import SafeUpdateMixin, LoginRequiredMixin
from app.core.generics.views import (
    CreateAPIEndpoint,
    RetrieveAPIEndpoint,
    UpdateAPIEndpoint,
)

from app.modules.accounts.models import User
from app.modules.accounts.schemas import UserRead, UserPublicCreate, UserUpdate
from app.modules.accounts.dependencies import get_current_user, get_user_service
from app.modules.accounts.services import UserService


router = APIRouter()


class Register(CreateAPIEndpoint):
    path = "/register"
    response_model = UserRead

    service: UserService = Depends(get_user_service)

    async def handle(self, user_in: UserPublicCreate) -> Any:
        return await self.service.register_user(user_in)


class GetMe(LoginRequiredMixin, RetrieveAPIEndpoint):
    path = "/me"
    response_model = UserRead

    async def handle(self) -> Any:
        return self.current_user


class UpdateMe(LoginRequiredMixin, UpdateAPIEndpoint, SafeUpdateMixin):
    path = "/me"
    response_model = UserRead

    service: UserService = Depends(get_user_service)

    forbidden_fields = {
        "id", "role", "is_active", "is_verified", "is_superuser",
        "is_staff", "hashed_password", "failed_login_count",
        "locked_until", "created_at", "updated_at",
    }
    password_hasher = staticmethod(hash_password)

    async def handle(self, user_in: UserUpdate) -> Any:
        data = self.clean(user_in.model_dump(exclude_unset=True))
        return await self.service.user_repository.update_user(self.current_user, data)


Register.register(router)
GetMe.register(router)
UpdateMe.register(router)