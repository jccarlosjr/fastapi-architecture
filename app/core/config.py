import json

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config : SettingsConfigDict = SettingsConfigDict(
        env_file='.env',
        extra="ignore"
    )

    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    DATABASE_URL: str
    REDIS_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: list[str] = []
    TRUSTED_HOSTS: list[str] = ["*"]

    RATE_LIMIT_LOGIN_MAX_ATTEMPTS: int = 5
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 900

    RATE_LIMIT_GLOBAL_MAX_REQUESTS: int = 100
    RATE_LIMIT_GLOBAL_WINDOW_SECONDS: int = 60

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            if not value.startswith("["):
                return [item.strip() for item in value.split(",")]
            parsed_value = json.loads(value)
            if isinstance(parsed_value, list):
                return [str(item) for item in parsed_value]
            return [str(parsed_value)]
        return value

    @field_validator("TRUSTED_HOSTS", mode="before")
    @classmethod
    def assemble_trusted_host(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            if not value.startswith("["):
                return [item.strip() for item in value.split(",")]
            parsed_value = json.loads(value)
            if isinstance(parsed_value, list):
                return [str(item) for item in parsed_value]
            return [str(parsed_value)]
        return value

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.ENVIRONMENT in ("production", "staging"):
            if self.DEBUG:
                raise ValueError(
                    "DEBUG must be False in production/staging environment"
                )
            if len(self.JWT_SECRET_KEY) < 32:
                raise ValueError(
                    "JWT_SECRET_KEY must be at least 32 characters long in production/staging environment"
                )
            if not self.CORS_ORIGINS or "*" in self.CORS_ORIGINS:
                raise ValueError(
                    "CORS_ORIGINS must be defined in production/staging environment"
                )
            if not self.TRUSTED_HOSTS or "*" in self.TRUSTED_HOSTS:
                raise ValueError(
                    "TRUSTED_HOSTS must be defined in production/staging environment"
                )
        return self


settings: Settings = Settings()
