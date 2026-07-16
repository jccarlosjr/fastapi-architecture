import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.generics.models import BaseModel

if TYPE_CHECKING:
    from app.modules.groups.models import Group
    from app.modules.permissions.models import Permission


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), index=True, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        )
    groups: Mapped[list["Group"]] = relationship(secondary="user_groups", back_populates="users")
    user_permissions: Mapped[list["Permission"]] = relationship(
        secondary="user_permissions",
        back_populates="users"
    )

    def has_permission(self, codename: str) -> bool:
        """
        Check if the user has a specific permission.
        Superusers have all permissions.
        """
        if self.is_superuser:
            return True
        
        # Check direct user permissions
        for perm in self.user_permissions:
            if perm.codename == codename:
                return True
                
        # Check group permissions
        for group in self.groups:
            for perm in group.permissions:
                if perm.codename == codename:
                    return True
                    
        return False
