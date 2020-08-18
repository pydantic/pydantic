from pydantic import (
    CommaSeparatedStripped,
    BaseSettings,
    RedisDsn,
)


class Settings(BaseSettings):
    environment: str = 'development'
    api_key: str
    redis_dsn: RedisDsn = 'redis://user:pass@localhost:6379/1'
    timeout_seconds: int = 60
    cors_origins: CommaSeparatedStripped[str] = []

    class Config:
        env_file = 'settings.env'
        env_file_encoding = 'utf-8'


print(Settings().dict())
