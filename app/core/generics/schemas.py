import uuid
from datetime import datetime
from typing import Any, Optional, Type

from pydantic import BaseModel, ConfigDict, create_model


class ORMBaseSchema(BaseModel):
    """Base para todo schema que lê/escreve a partir de um model ORM."""
    model_config = ConfigDict(from_attributes=True)


class ReadSchemaMixin(ORMBaseSchema):
    """Mixin com os campos que todo Read schema herda do BaseModel genérico."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


def crud_schemas(cls: Type[BaseModel]) -> Type[BaseModel]:
    """
    A class decorator that dynamically generates and attaches Create, Update, and Read schemas
    to the decorated base schema class.
    
    Usage:
        @crud_schemas
        class ItemBase(BaseModel):
            name: str
            price: float
            
        # The following classes are generated and accessible as attributes:
        # ItemBase.Create  -> (ItemCreate)
        # ItemBase.Update  -> (ItemUpdate, all fields optional)
        # ItemBase.Read    -> (ItemRead, with id, created_at, updated_at)
    """
    # 1. Create Schema (inherits from cls)
    create_name = f"{cls.__name__.replace('Base', '')}Create"
    create_schema = type(create_name, (cls,), {})
    setattr(cls, "Create", create_schema)

    # 2. Update Schema (makes all fields of cls optional)
    update_fields = {}
    for name, field in cls.model_fields.items():
        ann = field.annotation
        update_fields[name] = (Optional[ann], None)
        
    update_name = f"{cls.__name__.replace('Base', '')}Update"
    update_schema = create_model(update_name, __config__=cls.model_config, **update_fields)
    setattr(cls, "Update", update_schema)

    # 3. Read Schema (inherits from cls + ReadSchemaMixin)
    read_name = f"{cls.__name__.replace('Base', '')}Read"
    read_schema = type(read_name, (ReadSchemaMixin, cls), {})
    setattr(cls, "Read", read_schema)

    return cls
