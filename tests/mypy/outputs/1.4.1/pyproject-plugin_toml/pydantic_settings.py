from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    foo: str


s = Settings()

s = Settings(foo='test', _case_sensitive=True, _env_prefix='test__', _env_file='test')

s = Settings(foo='test', _case_sensitive=1, _env_prefix=2, _env_file=3)
# MYPY: error: Argument "_case_sensitive" to "Settings" has incompatible type "int"; expected "bool | None"  [arg-type]
# MYPY: error: Argument "_env_prefix" to "Settings" has incompatible type "int"; expected "str | None"  [arg-type]
# MYPY: error: Argument "_env_file" to "Settings" has incompatible type "int"; expected "Path | str | list[Path | str] | tuple[Path | str, ...] | None"  [arg-type]


class SettingsWithConfigDict(BaseSettings):
    bar: str

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


scd = SettingsWithConfigDict()
