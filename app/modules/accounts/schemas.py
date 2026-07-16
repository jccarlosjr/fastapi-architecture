import re
import uuid
from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.core.generics.schemas import ReadSchemaMixin
from app.modules.groups.schemas import GroupRead
from app.modules.permissions.schemas import PermissionRead


def normalize_email(value: str) -> str:
    """Normalize email to lower case and strip whitespace."""
    if isinstance(value, str):
        return value.strip().lower()
    return value


def validate_password_strength(value: str) -> str:
    """Verify password contains lower, upper, digit, and special characters."""
    if value is None:
        return value

    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[0-9]", value):
        raise ValueError("Password must contain at least one number")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        raise ValueError("Password must contain at least one special character")
    return value


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)

    @field_validator("email", mode="before")
    @classmethod
    def email_to_lower(cls, value: str) -> str:
        return normalize_email(value)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    is_superuser: bool = False
    is_staff: bool = False
    groups: list[uuid.UUID] = Field(default_factory=list)
    user_permissions: list[uuid.UUID] = Field(default_factory=list)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "password": "Strongpassword123!",
                "is_superuser": False,
                "is_staff": False,
                "groups": [],
                "user_permissions": [],
            }
        }
    )


class UserPublicCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "password": "Strongpassword123!",
            }
        }
    )


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(None, min_length=1, max_length=255)
    password: str | None = Field(None, min_length=8)
    is_superuser: bool | None = None
    is_staff: bool | None = None
    groups: list[uuid.UUID] | None = None
    user_permissions: list[uuid.UUID] | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)

    @field_validator("email", mode="before")
    @classmethod
    def email_to_lower(cls, value: str) -> str:
        return normalize_email(value)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "John Doe",
                "password": "Strongpassword123!",
                "is_staff": True,
            }
        }
    )


class UserRead(ReadSchemaMixin, UserBase):
    role: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    is_staff: bool
    groups: list[GroupRead] = []
    user_permissions: list[PermissionRead] = []

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "e4b476fd-61b4-471b-a5cc-9c86953dc30e",
                "email": "usuario@exemplo.com",
                "full_name": "Fulano de Tal",
                "role": "user",
                "is_active": True,
                "is_verified": False,
                "is_superuser": False,
                "is_staff": False,
                "created_at": "2026-07-12T12:00:00Z",
                "updated_at": "2026-07-12T12:00:00Z",
                "groups": [],
                "user_permissions": [],
            }
        },
    )

    @model_validator(mode="before")
    @classmethod
    def preprocess_db_object(cls, data: Any) -> Any:
        if hasattr(data, "__dict__"):
            res = {}
            for field in cls.model_fields:
                if field in ("groups", "user_permissions"):
                    res[field] = getattr(data, field, [])
                else:
                    res[field] = getattr(data, field, None)
            return res
        return data
