from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    foo: str


s = Settings()

s = Settings(foo='test', _case_sensitive=True, _env_prefix='test__', _env_file='test')

s = Settings(foo='test', _case_sensitive=1, _env_prefix=2, _env_file=3)
