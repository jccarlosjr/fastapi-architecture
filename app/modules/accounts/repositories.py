import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.generics.repository import GenericRepository
from app.modules.groups.models import Group
from app.modules.accounts.models import User
from app.modules.accounts.schemas import UserCreate, UserPublicCreate


class UserRepository(GenericRepository[User]):
    model = User

    async def get_by_id_with_permissions(
        self, user_id: uuid.UUID
    ) -> User | None:
        """
        Get user by id with his permissions.
        """
        result = await self.session.execute(
            select(self.model)
            .options(
                selectinload(self.model.groups).selectinload(Group.permissions),
                selectinload(self.model.user_permissions),
            )
            .where(self.model.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """
        Get user by email.
        """
        clean_email = email.strip().lower()
        result = await self.session.execute(
            select(self.model).where(self.model.email == clean_email)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self, user_in: UserCreate | UserPublicCreate, hashed_password: str
    ) -> User:
        """
        Create a new user in the database.
        """
        db_obj = self.model(
            email=user_in.email.strip().lower(),
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role="user",
            is_active=True,
            is_verified=False,
        )
        self.session.add(db_obj)
        if self.auto_commit:
            await self.session.commit()
        else:
            await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def update_user(
        self, db_obj: User, obj_in: dict[str, Any]
    ) -> User:
        """
        Update an existing user in-place.
        """
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                if field == "email" and isinstance(value, str):
                    value = value.strip().lower()
                setattr(db_obj, field, value)

        self.session.add(db_obj)
        if self.auto_commit:
            await self.session.commit()
        else:
            await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj
