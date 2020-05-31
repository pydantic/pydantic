from pydantic import BaseSettings


class Settings(BaseSettings):
    redis_host = 'localhost'

    class Config:
        case_sensitive = True
