from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    foo: str


s = Settings()

s = Settings(foo='test', _case_sensitive=True, _env_prefix='test__', _env_file='test')

s = Settings(foo='test', _case_sensitive=1, _env_prefix=2, _env_file=3)


class SettingsWithConfigDict(BaseSettings):
    bar: str

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


scd = SettingsWithConfigDict()
