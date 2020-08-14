import os
from typing import Dict, List, Optional, Set

import pytest

from pydantic import BaseModel, BaseSettings, Field, NoneStr, ValidationError, dataclasses
from pydantic.env_settings import SettingsError, read_env_file
from pydantic.types import SecretBytes, SecretStr

try:
    import dotenv
except ImportError:
    dotenv = None


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


def test_nested_env_with_basemodel(env):
    class TopValue(BaseModel):
        apple: str
        banana: str

    class Settings(BaseSettings):
        top: TopValue

    with pytest.raises(ValidationError):
        Settings()
    env.set('top', '{"banana": "secret_value"}')
    s = Settings(top={'apple': 'value'})
    assert s.top == {'apple': 'value', 'banana': 'secret_value'}


def test_nested_env_with_dict(env):
    class Settings(BaseSettings):
        top: Dict[str, str]

    with pytest.raises(ValidationError):
        Settings()
    env.set('top', '{"banana": "secret_value"}')
    s = Settings(top={'apple': 'value'})
    assert s.top == {'apple': 'value', 'banana': 'secret_value'}


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
    assert Settings(foobar='abc').foobar == 'abc'


def test_env_inheritance(env):
    class SettingsParent(BaseSettings):
        foobar: str = 'parent default'

        class Config:
            fields = {'foobar': {'env': 'different'}}

    class SettingsChild(SettingsParent):
        foobar: str = 'child default'

    assert SettingsParent().foobar == 'parent default'
    assert SettingsParent(foobar='abc').foobar == 'abc'

    assert SettingsChild().foobar == 'child default'
    assert SettingsChild(foobar='abc').foobar == 'abc'
    env.set('different', 'env value')
    assert SettingsParent().foobar == 'env value'
    assert SettingsParent(foobar='abc').foobar == 'abc'
    assert SettingsChild().foobar == 'env value'
    assert SettingsChild(foobar='abc').foobar == 'abc'


def test_env_inheritance_field(env):
    class SettingsParent(BaseSettings):
        foobar: str = Field('parent default', env='foobar_env')

    class SettingsChild(SettingsParent):
        foobar: str = 'child default'

    assert SettingsParent().foobar == 'parent default'
    assert SettingsParent(foobar='abc').foobar == 'abc'

    assert SettingsChild().foobar == 'child default'
    assert SettingsChild(foobar='abc').foobar == 'abc'
    env.set('foobar_env', 'env value')
    assert SettingsParent().foobar == 'env value'
    assert SettingsParent(foobar='abc').foobar == 'abc'
    assert SettingsChild().foobar == 'child default'
    assert SettingsChild(foobar='abc').foobar == 'abc'


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


def test_aliases_warning(env):
    with pytest.warns(FutureWarning, match='aliases are no longer used by BaseSettings'):

        class Settings(BaseSettings):
            foobar: str = 'default value'

            class Config:
                fields = {'foobar': 'foobar_alias'}

    assert Settings().foobar == 'default value'
    env.set('foobar_alias', 'xxx')
    assert Settings().foobar == 'default value'
    assert Settings(foobar_alias='42').foobar == '42'


def test_aliases_no_warning(env):
    class Settings(BaseSettings):
        foobar: str = 'default value'

        class Config:
            fields = {'foobar': {'alias': 'foobar_alias', 'env': 'foobar_env'}}

    assert Settings().foobar == 'default value'
    assert Settings(foobar_alias='42').foobar == '42'
    env.set('foobar_alias', 'xxx')
    assert Settings().foobar == 'default value'
    env.set('foobar_env', 'xxx')
    assert Settings().foobar == 'xxx'
    assert Settings(foobar_alias='42').foobar == '42'


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


def test_case_insensitive(monkeypatch):
    class Settings1(BaseSettings):
        foo: str

    with pytest.warns(DeprecationWarning, match='Settings2: "case_insensitive" is deprecated on BaseSettings'):

        class Settings2(BaseSettings):
            foo: str

            class Config:
                case_insensitive = False

    assert Settings1.__config__.case_sensitive is False
    assert Settings2.__config__.case_sensitive is True


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

        def _build_values(self, init_kwargs, _env_file, _env_file_encoding, _secrets_dir):
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

        def _build_values(self, init_kwargs, _env_file, _env_file_encoding, _secrets_dir):
            config_settings = init_kwargs.pop('__config_settings__')
            return {**config_settings, **init_kwargs, **self._build_environ()}

    env.set('C', 'env setting c')

    config = {'a': 'config a', 'b': 'config b', 'c': 'config c'}
    s = Settings(__config_settings__=config, b='argument b', c='argument c')
    assert s.a == 'config a'
    assert s.b == 'argument b'
    assert s.c == 'env setting c'


test_env_file = """\
# this is a comment
A=good string
# another one, followed by whitespace

b='better string'
c="best string"
"""


@pytest.mark.skipif(not dotenv, reason='python-dotenv not installed')
def test_env_file_config(env, tmp_path):
    p = tmp_path / '.env'
    p.write_text(test_env_file)

    class Settings(BaseSettings):
        a: str
        b: str
        c: str

        class Config:
            env_file = p

    env.set('A', 'overridden var')

    s = Settings()
    assert s.a == 'overridden var'
    assert s.b == 'better string'
    assert s.c == 'best string'


@pytest.mark.skipif(not dotenv, reason='python-dotenv not installed')
def test_env_file_config_case_sensitive(tmp_path):
    p = tmp_path / '.env'
    p.write_text(test_env_file)

    class Settings(BaseSettings):
        a: str
        b: str
        c: str

        class Config:
            env_file = p
            case_sensitive = True

    with pytest.raises(ValidationError) as exc_info:
        Settings()
    assert exc_info.value.errors() == [{'loc': ('a',), 'msg': 'field required', 'type': 'value_error.missing'}]


@pytest.mark.skipif(not dotenv, reason='python-dotenv not installed')
def test_env_file_export(env, tmp_path):
    p = tmp_path / '.env'
    p.write_text(
        """\
export A='good string'
export B=better-string
export C="best string"
"""
    )

    class Settings(BaseSettings):
        a: str
        b: str
        c: str

        class Config:
            env_file = p

    env.set('A', 'overridden var')

    s = Settings()
    assert s.a == 'overridden var'
    assert s.b == 'better-string'
    assert s.c == 'best string'


@pytest.mark.skipif(not dotenv, reason='python-dotenv not installed')
def test_env_file_config_custom_encoding(tmp_path):
    p = tmp_path / '.env'
    p.write_text('pika=p!±@', encoding='latin-1')

    class Settings(BaseSettings):
        pika: str

        class Config:
            env_file = p
            env_file_encoding = 'latin-1'

    s = Settings()
    assert s.pika == 'p!±@'


@pytest.mark.skipif(not dotenv, reason='python-dotenv not installed')
def test_env_file_none(tmp_path):
    p = tmp_path / '.env'
    p.write_text('a')

    class Settings(BaseSettings):
        a: str = 'xxx'

    s = Settings(_env_file=p)
    assert s.a == 'xxx'


@pytest.mark.skipif(not dotenv, reason='python-dotenv not installed')
def test_env_file_override_file(tmp_path):
    p1 = tmp_path / '.env'
    p1.write_text(test_env_file)
    p2 = tmp_path / '.env.prod'
    p2.write_text('A="new string"')

    class Settings(BaseSettings):
        a: str

        class Config:
            env_file = str(p1)

    s = Settings(_env_file=p2)
    assert s.a == 'new string'


@pytest.mark.skipif(not dotenv, reason='python-dotenv not installed')
def test_env_file_override_none(tmp_path):
    p = tmp_path / '.env'
    p.write_text(test_env_file)

    class Settings(BaseSettings):
        a: str = None

        class Config:
            env_file = p

    s = Settings(_env_file=None)
    assert s.a is None


@pytest.mark.skipif(not dotenv, reason='python-dotenv not installed')
def test_env_file_not_a_file(env):
    class Settings(BaseSettings):
        a: str = None

    env.set('A', 'ignore non-file')
    s = Settings(_env_file='tests/')
    assert s.a == 'ignore non-file'


@pytest.mark.skipif(not dotenv, reason='python-dotenv not installed')
def test_read_env_file_cast_sensitive(tmp_path):
    p = tmp_path / '.env'
    p.write_text('a="test"\nB=123')

    assert read_env_file(p) == {'a': 'test', 'b': '123'}
    assert read_env_file(p, case_sensitive=True) == {'a': 'test', 'B': '123'}


@pytest.mark.skipif(not dotenv, reason='python-dotenv not installed')
def test_read_env_file_syntax_wrong(tmp_path):
    p = tmp_path / '.env'
    p.write_text('NOT_AN_ASSIGNMENT')

    assert read_env_file(p, case_sensitive=True) == {'NOT_AN_ASSIGNMENT': None}


@pytest.mark.skipif(not dotenv, reason='python-dotenv not installed')
def test_env_file_example(tmp_path):
    p = tmp_path / '.env'
    p.write_text(
        """\
# ignore comment
ENVIRONMENT="production"
REDIS_ADDRESS=localhost:6379
MEANING_OF_LIFE=42
MY_VAR='Hello world'
"""
    )

    class Settings(BaseSettings):
        environment: str
        redis_address: str
        meaning_of_life: int
        my_var: str

    s = Settings(_env_file=str(p))
    assert s.dict() == {
        'environment': 'production',
        'redis_address': 'localhost:6379',
        'meaning_of_life': 42,
        'my_var': 'Hello world',
    }


@pytest.mark.skipif(not dotenv, reason='python-dotenv not installed')
def test_env_file_custom_encoding(tmp_path):
    p = tmp_path / '.env'
    p.write_text('pika=p!±@', encoding='latin-1')

    class Settings(BaseSettings):
        pika: str

    with pytest.raises(UnicodeDecodeError):
        Settings(_env_file=str(p))

    s = Settings(_env_file=str(p), _env_file_encoding='latin-1')
    assert s.dict() == {'pika': 'p!±@'}


@pytest.mark.skipif(dotenv, reason='python-dotenv is installed')
def test_dotenv_not_installed(tmp_path):
    p = tmp_path / '.env'
    p.write_text('a=b')

    class Settings(BaseSettings):
        a: str

    with pytest.raises(ImportError, match=r'^python-dotenv is not installed, run `pip install pydantic\[dotenv\]`$'):
        Settings(_env_file=p)


def test_alias_set(env):
    class Settings(BaseSettings):
        foo: str = 'default foo'
        bar: str = 'bar default'

        class Config:
            fields = {'foo': {'env': 'foo_env'}}

    assert Settings.__fields__['bar'].name == 'bar'
    assert Settings.__fields__['bar'].alias == 'bar'
    assert Settings.__fields__['foo'].name == 'foo'
    assert Settings.__fields__['foo'].alias == 'foo'

    class SubSettings(Settings):
        spam: str = 'spam default'

    assert SubSettings.__fields__['bar'].name == 'bar'
    assert SubSettings.__fields__['bar'].alias == 'bar'
    assert SubSettings.__fields__['foo'].name == 'foo'
    assert SubSettings.__fields__['foo'].alias == 'foo'

    assert SubSettings().dict() == {'foo': 'default foo', 'bar': 'bar default', 'spam': 'spam default'}
    env.set('foo_env', 'fff')
    assert SubSettings().dict() == {'foo': 'fff', 'bar': 'bar default', 'spam': 'spam default'}
    env.set('bar', 'bbb')
    assert SubSettings().dict() == {'foo': 'fff', 'bar': 'bbb', 'spam': 'spam default'}
    env.set('spam', 'sss')
    assert SubSettings().dict() == {'foo': 'fff', 'bar': 'bbb', 'spam': 'sss'}


def test_prefix_on_parent(env):
    class MyBaseSettings(BaseSettings):
        var: str = 'old'

    class MySubSettings(MyBaseSettings):
        class Config:
            env_prefix = 'PREFIX_'

    assert MyBaseSettings().dict() == {'var': 'old'}
    assert MySubSettings().dict() == {'var': 'old'}
    env.set('PREFIX_VAR', 'new')
    assert MyBaseSettings().dict() == {'var': 'old'}
    assert MySubSettings().dict() == {'var': 'new'}


def test_frozenset(env):
    class Settings(BaseSettings):
        foo: str = 'default foo'

        class Config:
            fields = {'foo': {'env': frozenset(['foo_a', 'foo_b'])}}

    assert Settings.__fields__['foo'].field_info.extra['env_names'] == frozenset({'foo_a', 'foo_b'})

    assert Settings().dict() == {'foo': 'default foo'}
    env.set('foo_a', 'x')
    assert Settings().dict() == {'foo': 'x'}


def test_secrets_secret_str(tmp_path):
    p = tmp_path / 'foo'
    p.write_text('foo_secret_value_str')

    class Settings(BaseSettings):
        foo: SecretStr

        class Config:
            secrets_dir = tmp_path

    assert Settings().dict() == {'foo': SecretStr('foo_secret_value_str')}


def test_secrets_secret_bytes(tmp_path):
    p = tmp_path / 'foo'
    p.write_bytes(b'foo_secret_value_bytes')

    class Settings(BaseSettings):
        foo: SecretBytes

        class Config:
            secrets_dir = tmp_path

    assert Settings().dict() == {'foo': SecretBytes(b'foo_secret_value_bytes')}


def test_secrets_skip_non_secret(tmp_path):
    p1 = tmp_path / 'foo'
    p1.write_text('foo_secret_value_str')
    p2 = tmp_path / 'bar'
    p2.write_text('bar_secret_value_str')

    class Settings(BaseSettings):
        foo: SecretStr
        bar: Optional[str]

        class Config:
            secrets_dir = tmp_path

    with pytest.warns(Warning, match='field was not of type "SecretStr" or "SecretBytes"'):
        settings = Settings()

    assert settings.dict() == {'foo': SecretStr('foo_secret_value_str'), 'bar': None}


def test_secrets_missing(tmp_path):
    class Settings(BaseSettings):
        foo: SecretStr

        class Config:
            secrets_dir = tmp_path

    with pytest.raises(ValidationError) as exc_info:
        Settings()
    assert exc_info.value.errors() == [{'loc': ('foo',), 'msg': 'field required', 'type': 'value_error.missing'}]


def test_secrets_invalid_secrets_dir(tmp_path):
    p1 = tmp_path / 'foo'
    p1.write_text('foo_secret_value_str')

    class Settings(BaseSettings):
        foo: SecretStr

        class Config:
            secrets_dir = p1

    with pytest.raises(ValidationError) as exc_info:
        Settings()
    assert exc_info.value.errors() == [{'loc': ('foo',), 'msg': 'field required', 'type': 'value_error.missing'}]


@pytest.mark.skipif(not dotenv, reason='python-dotenv not installed')
def test_secrets_dotenv_precedence(tmp_path):
    s = tmp_path / 'foo'
    s.write_text('foo_secret_value_str')

    e = tmp_path / '.env'
    e.write_text('foo=foo_env_value_str')

    class Settings(BaseSettings):
        foo: SecretStr

        class Config:
            secrets_dir = tmp_path

    assert Settings(_env_file=e).dict() == {'foo': SecretStr('foo_env_value_str')}
