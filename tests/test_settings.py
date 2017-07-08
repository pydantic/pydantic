import pytest

from pydantic import BaseSettings, ValidationError


class SimpleSettings(BaseSettings):
    apple: str = ...


def test_sub_env(env):
    env.set('APP_APPLE', 'hello')
    s = SimpleSettings()
    assert s.apple == 'hello'


def test_sub_env_override(env):
    env.set('APP_APPLE', 'hello')
    s = SimpleSettings(apple='goodbye')
    assert s.apple == 'goodbye'


def test_sub_env_missing():
    with pytest.raises(ValidationError) as exc_info:
        SimpleSettings()
    assert """\
error validating input
apple:
  None is not an allow value (error_type=TypeError track=str)\
""" == str(exc_info.value)


def test_other_setting(env):
    with pytest.raises(ValidationError):
        SimpleSettings(apple='a', foobar=42)


def test_env_with_aliass(env):
    class Settings(BaseSettings):
        apple: str = ...

        class Config:
            fields = {
                'apple': 'BOOM'
            }
    env.set('BOOM', 'hello')
    assert Settings().apple == 'hello'
