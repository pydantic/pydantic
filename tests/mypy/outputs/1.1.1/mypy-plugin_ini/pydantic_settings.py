from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    foo: str


s = Settings()

s = Settings(foo='test', _case_sensitive=True, _env_prefix='test__', _env_file='test')

s = Settings(foo='test', _case_sensitive=1, _env_prefix=2, _env_file=3)
# MYPY: error: Argument "_case_sensitive" to "Settings" has incompatible type "int"; expected "Optional[bool]"  [arg-type]
# MYPY: error: Argument "_env_prefix" to "Settings" has incompatible type "int"; expected "Optional[str]"  [arg-type]
# MYPY: error: Argument "_env_file" to "Settings" has incompatible type "int"; expected "Optional[Union[Path, str, List[Union[Path, str]], Tuple[Union[Path, str], ...]]]"  [arg-type]
