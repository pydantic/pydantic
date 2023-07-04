from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    foo: str


s = Settings()
# MYPY: error: Missing named argument "foo" for "Settings"  [call-arg]
