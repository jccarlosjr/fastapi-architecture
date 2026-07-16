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


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_lenght=1)

    @field_validator("email", mode="before")
    @classmethod
    def email_to_lower(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "email": "john_doe@example.com",
                "password": "Strongpassword123!"
            }
        }
    )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900
            }
        }
    )


class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Opaque refresh token UUID")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "refresh_token": "3f4b82d9-1c88-4cde-80df-5645e7aa7c19"
            }
        }
    )
