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
    assert exc_info.value.args[0] == ('1 error validating input: {"apple": {"error_msg": "None is not an allow value", '
                                      '"error_type": "TypeError", "index": null, "track": "str"}}')
