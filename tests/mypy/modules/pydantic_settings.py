from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    foo: str


s = Settings()
