import os
from typing import List, Set

import pytest

from pydantic import BaseModel, BaseSettings, Field, NoneStr, ValidationError, dataclasses
from pydantic.env_settings import SettingsError


class SimpleSettings(BaseSettings):
    apple: str


def test_sub_env(env):
    env.set('apple', 'hello')
    s = SimpleSettings()
    assert s.apple == 'hello'


def test_sub_env_override(env):
    env.set('apple', 'hello')
    s = SimpleSettings(apple='goodbye')
    assert s.apple == 'goodbye'


def test_sub_env_missing():
    with pytest.raises(ValidationError) as exc_info:
        SimpleSettings()
    assert exc_info.value.errors() == [{'loc': ('apple',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_other_setting():
    with pytest.raises(ValidationError):
        SimpleSettings(apple='a', foobar=42)


def test_with_prefix(env):
    class Settings(BaseSettings):
        apple: str

        class Config:
            env_prefix = 'foobar_'

    with pytest.raises(ValidationError):
        Settings()
    env.set('foobar_apple', 'has_prefix')
    s = Settings()
    assert s.apple == 'has_prefix'


class DateModel(BaseModel):
    pips: bool = False


class ComplexSettings(BaseSettings):
    apples: List[str] = []
    bananas: Set[int] = set()
    carrots: dict = {}
    date: DateModel = DateModel()


def test_list(env):
    env.set('apples', '["russet", "granny smith"]')
    s = ComplexSettings()
    assert s.apples == ['russet', 'granny smith']
    assert s.date.pips is False


def test_set_dict_model(env):
    env.set('bananas', '[1, 2, 3, 3]')
    env.set('CARROTS', '{"a": null, "b": 4}')
    env.set('daTE', '{"pips": true}')
    s = ComplexSettings()
    assert s.bananas == {1, 2, 3}
    assert s.carrots == {'a': None, 'b': 4}
    assert s.date.pips is True


def test_invalid_json(env):
    env.set('apples', '["russet", "granny smith",]')
    with pytest.raises(SettingsError, match='error parsing JSON for "apples"'):
        ComplexSettings()


def test_required_sub_model(env):
    class Settings(BaseSettings):
        foobar: DateModel

    with pytest.raises(ValidationError):
        Settings()
    env.set('FOOBAR', '{"pips": "TRUE"}')
    s = Settings()
    assert s.foobar.pips is True


def test_non_class(env):
    class Settings(BaseSettings):
        foobar: NoneStr

    env.set('FOOBAR', 'xxx')
    s = Settings()
    assert s.foobar == 'xxx'


def test_env_str(env):
    class Settings(BaseSettings):
        apple: str = ...

        class Config:
            fields = {'apple': {'env': 'BOOM'}}

    env.set('BOOM', 'hello')
    assert Settings().apple == 'hello'


def test_env_list(env):
    class Settings(BaseSettings):
        foobar: str

        class Config:
            fields = {'foobar': {'env': ['different1', 'different2']}}

    env.set('different1', 'value 1')
    env.set('different2', 'value 2')
    s = Settings()
    assert s.foobar == 'value 1'


def test_env_list_field(env):
    class Settings(BaseSettings):
        foobar: str = Field(..., env='foobar_env_name')

    env.set('FOOBAR_ENV_NAME', 'env value')
    s = Settings()
    assert s.foobar == 'env value'


def test_env_list_last(env):
    class Settings(BaseSettings):
        foobar: str

        class Config:
            fields = {'foobar': {'env': ['different2']}}

    env.set('different1', 'value 1')
    env.set('different2', 'value 2')
    s = Settings()
    assert s.foobar == 'value 2'


def test_env_invalid(env):
    with pytest.raises(TypeError, match=r'invalid field env: 123 \(int\); should be string, list or set'):

        class Settings(BaseSettings):
            foobar: str

            class Config:
                fields = {'foobar': {'env': 123}}


def test_env_field(env):
    with pytest.raises(TypeError, match=r'invalid field env: 123 \(int\); should be string, list or set'):

        class Settings(BaseSettings):
            foobar: str = Field(..., env=123)


def test_aliases_no_effect(env):
    class Settings(BaseSettings):
        foobar: str = 'default value'

        class Config:
            fields = {'foobar': 'different'}

    env.set('different', 'xxx')
    s = Settings()
    assert s.foobar == 'default value'


def test_case_sensitive(monkeypatch):
    class Settings(BaseSettings):
        foo: str

        class Config:
            case_sensitive = True

    # Need to patch os.environ to get build to work on Windows, where os.environ is case insensitive
    monkeypatch.setattr(os, 'environ', value={'Foo': 'foo'})
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    assert exc_info.value.errors() == [{'loc': ('foo',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_nested_dataclass(env):
    @dataclasses.dataclass
    class MyDataclass:
        foo: int
        bar: str

    class Settings(BaseSettings):
        n: MyDataclass

    env.set('N', '[123, "bar value"]')
    s = Settings()
    assert isinstance(s.n, MyDataclass)
    assert s.n.foo == 123
    assert s.n.bar == 'bar value'


def test_env_takes_precedence(env):
    class Settings(BaseSettings):
        foo: int
        bar: str

        def _build_values(self, init_kwargs):
            return {**init_kwargs, **self._build_environ()}

    env.set('BAR', 'env setting')

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

    env.set('C', 'env setting c')

    config = {'a': 'config a', 'b': 'config b', 'c': 'config c'}
    s = Settings(__config_settings__=config, b='argument b', c='argument c')
    assert s.a == 'config a'
    assert s.b == 'argument b'
    assert s.c == 'env setting c'
