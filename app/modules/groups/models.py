import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.core.generics.models import BaseModel

if TYPE_CHECKING:
    from app.modules.permissions.models import Permission
    from app.modules.accounts.models import User

# Associative table for User and Group
user_groups = Table(
    "user_groups",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
)

class Group(BaseModel):
    __tablename__ = "groups"
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)

    # Many-to-Many relationship with User
    users: Mapped[list["User"]] = relationship(
        secondary=user_groups, back_populates="groups"
    )

    # Many-to-Many relationship with Permission
    permissions: Mapped[list["Permission"]] = relationship(
        secondary="group_permissions", back_populates="groups"
    )


