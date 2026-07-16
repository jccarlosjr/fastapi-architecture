import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.generics.schemas import ORMBaseSchema
from app.modules.permissions.schemas import PermissionRead

class GroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)


class GroupCreate(GroupBase):
    name: str | None = Field(None, min_length=1, max_length=150)
    permissions: list[uuid.UUID] | None = Field(
        None, description="List of UUIDs of associated permissions"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Managers",
                "permissions": ["8d5f1b2c-1a9e-4b6c-8a1d-2c3b4d5e6f7g"]
            }
        }
    )


class GroupUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    permissions: list[uuid.UUID] | None = Field(
        None, description="List of UUIDs of permissions"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Managers",
                "permissions": ["8d5f1b2c-1a9e-4b6c-8a1d-2c3b4d5e6f7g"]
            }
        }
    )


class GroupRead(ORMBaseSchema, GroupBase):
    id: uuid.UUID
    permissions: list[PermissionRead] = []

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "8d5f1b2c-1a9e-4b6c-8a1d-2c3b4d5e6f7g",
                "name": "Managers",
                "permissions": [
                    {
                        "id": "8d5f1b2c-1a9e-4b6c-8a1d-2c3b4d5e6f7g",
                        "name": "Can add User",
                        "codename": "add_user"
                    }
                ]
            }
        }
    )

    @model_validator(mode="before")
    @classmethod
    def preprocess_db_object(cls, data: Any) -> Any:
        if hasattr(data, "__dict__"):
            res = {}
            for field in cls.model_fields:
                if field == "permissions":
                    res[field] = getattr(data, field, [])
                else:
                    res[field] = getattr(data, field, None)
            return res
        return data
