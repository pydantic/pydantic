from typing import List, Set

import pytest

from pydantic import BaseSettings, ValidationError
from pydantic.env_settings import SettingsError


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


class ComplexSettings(BaseSettings):
    apples: List[str] = []
    bananas: Set[int] = set()
    carrots: dict = {}
    dates: SimpleSettings = SimpleSettings(apple='foobar')


def test_list(env):
    env.set('APP_APPLES', '["russet", "granny smith"]')
    s = ComplexSettings()
    assert s.apples == ['russet', 'granny smith']


def test_set_dict_model(env):
    env.set('APP_BANANAS', '[1, 2, 3, 3]')
    env.set('APP_CARROTS', '{"a": null, "b": 4}')
    env.set('APP_DATES', '{"apple": "snap"}')
    s = ComplexSettings()
    assert s.bananas == {1, 2, 3}
    assert s.carrots == {'a': None, 'b': 4}
    assert s.dates.apple == 'snap'


def test_invalid_json(env):
    env.set('APP_APPLES', '["russet", "granny smith",]')
    with pytest.raises(SettingsError):
        ComplexSettings()
