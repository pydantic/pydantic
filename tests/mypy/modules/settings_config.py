from pydantic import BaseSettings


class Settings(BaseSettings):
    class Config(BaseSettings.Config):
        env_file = '.env'
        env_file_encoding = 'utf-8'
