import uuid
from pydantic import BaseModel, Field
from app.core.generics.schemas import crud_schemas


@crud_schemas
class PermissionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=25)
    codename: str = Field(..., min_length=1, max_length=100)


PermissionCreate = PermissionBase.Create
PermissionUpdate = PermissionBase.Update
PermissionRead = PermissionBase.Read

PermissionCreate.model_config["json_schema_extra"] = {
    "example": {
        "name": "Can add user",
        "codename": "add_user"
    }
}

PermissionUpdate.model_config["json_schema_extra"] = {
    "example": {
        "name": "Can change user",
        "codename": "change_user"
    }
}

PermissionRead.model_config["json_schema_extra"] = {
    "example": {
        "id": "8d5f1b2c-1a9e-4b6c-8a1d-2c3b4d5e6f7g",
        "name": "Can read user",
        "codename": "read_user"
    }
}
