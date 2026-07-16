from typing import Callable, ClassVar, Optional
from fastapi import Depends, HTTPException, status
from app.modules.accounts.dependencies import get_current_user
from app.modules.accounts.models import User


class SafeUpdateMixin:
    """
    Optional mixin for update endpoints.

    Provides a `clean()` helper that strips out fields the client should
    never be able to set directly (id, role, is_active, ...) and hashes
    the password if one was sent — so this logic isn't repeated in every
    update endpoint across the project.
    """

    forbidden_fields: ClassVar[set[str]] = set()
    password_hasher: ClassVar[Optional[Callable[[str], str]]] = None

    def clean(self, data: dict) -> dict:
        """Remove forbidden fields and hash the password, if present."""
        for field in self.forbidden_fields:
            data.pop(field, None)

        password = data.pop("password", None)
        if password and self.password_hasher:
            data["hashed_password"] = self.password_hasher(password)

        return data


class LoginRequiredMixin:
    """Requires the user to be logged in."""
    current_user: User = Depends(get_current_user)

    async def check_access(self) -> None:
        if not self.current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        await super().check_access()


class StaffRequiredMixin(LoginRequiredMixin):
    """Requires the logged in user to be staff or superuser."""
    async def check_access(self) -> None:
        await super().check_access()
        if not (self.current_user.is_staff or self.current_user.is_superuser):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Staff privileges required",
            )


class AdminRequiredMixin(LoginRequiredMixin):
    """Requires the logged in user to be superuser."""
    async def check_access(self) -> None:
        await super().check_access()
        if not self.current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required",
            )
