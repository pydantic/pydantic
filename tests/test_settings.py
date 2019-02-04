from typing import List, Set

import pytest

from pydantic import BaseModel, BaseSettings, NoneStr, ValidationError, dataclasses
from pydantic.env_settings import SettingsError


class SimpleSettings(BaseSettings):
    apple: str


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
    assert exc_info.value.errors() == [{'loc': ('apple',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_other_setting(env):
    with pytest.raises(ValidationError):
        SimpleSettings(apple='a', foobar=42)


def test_env_with_aliass(env):
    class Settings(BaseSettings):
        apple: str = ...

        class Config:
            fields = {'apple': 'BOOM'}

    env.set('BOOM', 'hello')
    assert Settings().apple == 'hello'


class DateModel(BaseModel):
    pips: bool = False


class ComplexSettings(BaseSettings):
    apples: List[str] = []
    bananas: Set[int] = set()
    carrots: dict = {}
    date: DateModel = DateModel()


def test_list(env):
    env.set('APP_APPLES', '["russet", "granny smith"]')
    s = ComplexSettings()
    assert s.apples == ['russet', 'granny smith']
    assert s.date.pips is False


def test_set_dict_model(env):
    env.set('APP_BANANAS', '[1, 2, 3, 3]')
    env.set('APP_CARROTS', '{"a": null, "b": 4}')
    env.set('APP_DATE', '{"pips": true}')
    s = ComplexSettings()
    assert s.bananas == {1, 2, 3}
    assert s.carrots == {'a': None, 'b': 4}
    assert s.date.pips is True


def test_invalid_json(env):
    env.set('APP_APPLES', '["russet", "granny smith",]')
    with pytest.raises(SettingsError):
        ComplexSettings()


def test_required_sub_model(env):
    class Settings(BaseSettings):
        foobar: DateModel

    with pytest.raises(ValidationError):
        Settings()
    env.set('APP_FOOBAR', '{"pips": "TRUE"}')
    s = Settings()
    assert s.foobar.pips is True


def test_non_class(env):
    class Settings(BaseSettings):
        foobar: NoneStr

    env.set('APP_FOOBAR', 'xxx')
    s = Settings()
    assert s.foobar == 'xxx'


def test_alias_matches_name(env):
    class Settings(BaseSettings):
        foobar: str

        class Config:
            fields = {'foobar': 'foobar'}

    env.set('foobar', 'xxx')
    s = Settings()
    assert s.foobar == 'xxx'


def test_case_insensitive(env):
    class Settings(BaseSettings):
        foo: str
        bAR: str

        class Config:
            case_insensitive = True

    env.set('apP_foO', 'foo')
    env.set('app_bar', 'bar')
    s = Settings()
    assert s.foo == 'foo'
    assert s.bAR == 'bar'


def test_nested_dataclass(env):
    @dataclasses.dataclass
    class MyDataclass:
        foo: int
        bar: str

    class Settings(BaseSettings):
        n: MyDataclass

    env.set('APP_N', '[123, "bar value"]')
    s = Settings()
    assert isinstance(s.n, MyDataclass)
    assert s.n.foo == 123
    assert s.n.bar == 'bar value'


def test_config_file_settings(env):
    class Settings(BaseSettings):
        foo: int
        bar: str

        def _build_values(self, init_kwargs):
            return {**init_kwargs, **self._build_environ()}

    env.set('APP_BAR', 'env setting')

    s = Settings(foo='123', bar='argument')
    assert s.foo == 123
    assert s.bar == 'env setting'


def test_config_file_settings_nornir(env):
    """
    See https://github.com/samuelcolvin/pydantic/pull/341#issuecomment-450378771
    """

    class Settings(BaseSettings):
        a: str
        b: str
        c: str

        def _build_values(self, init_kwargs):
            config_settings = init_kwargs.pop('__config_settings__')
            return {**config_settings, **init_kwargs, **self._build_environ()}

    env.set('APP_C', 'env setting c')

    config = {'a': 'config a', 'b': 'config b', 'c': 'config c'}
    s = Settings(__config_settings__=config, b='argument b', c='argument c')
    assert s.a == 'config a'
    assert s.b == 'argument b'
    assert s.c == 'env setting c'
