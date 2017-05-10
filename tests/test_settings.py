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
1 error validating input
apple:
  None is not an allow value (error_type=TypeError track=str)\
""" == str(exc_info.value)
