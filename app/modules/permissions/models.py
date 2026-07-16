import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.core.generics.models import BaseModel

if TYPE_CHECKING:
    from app.modules.groups.models import Group
    from app.modules.accounts.models import User

# Associative table for Group and Permission
group_permissions = Table(
    "group_permissions",
    Base.metadata,
    Column(
        "group_id", 
        ForeignKey("groups.id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "permission_id", 
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True
    ),
)

# Associative table for User and Permission
user_permissions = Table(
    "user_permissions",
    Base.metadata,
    Column(
        "user_id", 
        ForeignKey("users.id", ondelete="CASCADE"), 
        primary_key=True
    ),
    Column(
        "permission_id", 
        ForeignKey("permissions.id", ondelete="CASCADE"), 
        primary_key=True
    ),
)

class Permission(BaseModel):
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    codename: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    # Many-to-many relationship with User
    users: Mapped[list["User"]] = relationship(
        secondary=user_permissions, 
        back_populates="user_permissions"
    )

    # Many-to-many relationship with Group
    groups: Mapped[list["Group"]] = relationship(
        secondary=group_permissions,
        back_populates="permissions"
    )
