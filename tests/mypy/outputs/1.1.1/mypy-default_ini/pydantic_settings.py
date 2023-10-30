from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    foo: str


s = Settings()
# MYPY: error: Missing named argument "foo" for "Settings"  [call-arg]

s = Settings(foo='test', _case_sensitive=True, _env_prefix='test__', _env_file='test')
# MYPY: error: Unexpected keyword argument "_case_sensitive" for "Settings"  [call-arg]
# MYPY: error: Unexpected keyword argument "_env_prefix" for "Settings"  [call-arg]
# MYPY: error: Unexpected keyword argument "_env_file" for "Settings"  [call-arg]

s = Settings(foo='test', _case_sensitive=1, _env_prefix=2, _env_file=3)
# MYPY: error: Unexpected keyword argument "_case_sensitive" for "Settings"  [call-arg]
# MYPY: error: Unexpected keyword argument "_env_prefix" for "Settings"  [call-arg]
# MYPY: error: Unexpected keyword argument "_env_file" for "Settings"  [call-arg]


class SettingsWithConfigDict(BaseSettings):
    bar: str

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


scd = SettingsWithConfigDict()
# MYPY: error: Missing named argument "bar" for "SettingsWithConfigDict"  [call-arg]
