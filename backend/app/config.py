from functools import lru_cache
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = 'postgresql+psycopg://badabee:badabee@localhost:5432/badabee'
    jwt_secret: str = Field(min_length=32)
    distress_ingest_key: str = Field(min_length=32)
    jwt_issuer: str = 'badabee'
    jwt_audience: str = 'badabee-web'
    token_minutes: int = Field(default=30, ge=1, le=120)
    cors_origins: list[str] = ['http://localhost:5173']
    demo_seed_enabled: bool = False

    @model_validator(mode='after')
    def independent_secrets(self):
        if self.jwt_secret.startswith('replace-with-') or self.distress_ingest_key.startswith('replace-with-'):
            raise ValueError('Replace example secrets with independent random secrets')
        if self.jwt_secret == self.distress_ingest_key:
            raise ValueError('JWT and integration credentials must be different')
        return self


@lru_cache
def settings():
    return Settings()
