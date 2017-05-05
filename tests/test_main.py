from collections import OrderedDict

import pytest

from pydantic import BaseModel, ConfigError, NoneBytes, NoneStr, ValidationError


class UltraSimpleModel(BaseModel):
    a: float = ...
    b: int = 10


def test_ultra_simple_success():
    m = UltraSimpleModel(a=10.2)
    assert m.a == 10.2
    assert m.b == 10


def test_ultra_simple_missing():
    with pytest.raises(ValidationError) as exc_info:
        UltraSimpleModel()
    assert exc_info.value.args[0] == '1 error validating input: {"a": {"msg": "field required", "type": "Missing"}}'


def test_ultra_simple_failed():
    with pytest.raises(ValidationError) as exc_info:
        UltraSimpleModel(a='x', b='x')
    assert exc_info.value.errors == OrderedDict(
        [
            ('a', {'type': 'ValueError', 'msg': "could not convert string to float: 'x'", 'validator': 'float'}),
            ('b', {'type': 'ValueError', 'msg': "invalid literal for int() with base 10: 'x'", 'validator': 'int'})
        ]
    )


def test_ultra_simple_repr():
    m = UltraSimpleModel(a=10.2)
    assert repr(m) == '<UltraSimpleModel a=10.2 b=10>'
    assert repr(m.fields['a']) == ("<Field a: type='float', required=True, "
                                   "validators=['float', 'number_size_validator']>")


class ConfigModel(UltraSimpleModel):
    class Config:
        raise_exception = False


def test_config_doesnt_raise():
    m = ConfigModel()
    assert m.errors == OrderedDict([('a', {'type': 'Missing', 'msg': 'field required'})])
    assert m.config.raise_exception is False
    assert m.config.max_anystr_length == 65536


class NoneCheckModel(BaseModel):
    existing_str_value = 'foo'
    required_str_value: str = ...
    required_str_none_value: NoneStr = ...
    existing_bytes_value = b'foo'
    required_bytes_value: bytes = ...
    required_bytes_none_value: NoneBytes = ...

    class Config:
        raise_exception = False


def test_nullable_strings_success():
    m = NoneCheckModel(
        required_str_value='v1',
        required_str_none_value=None,
        required_bytes_value='v2',
        required_bytes_none_value=None,
    )
    assert m.required_str_value == 'v1'
    assert m.required_str_none_value is None
    assert m.required_bytes_value == b'v2'
    assert m.required_bytes_none_value is None


def test_nullable_strings_fails():
    m = NoneCheckModel(
        required_str_value=None,
        required_str_none_value=None,
        required_bytes_value=None,
        required_bytes_none_value=None,
    )
    assert m.errors == OrderedDict(
        [
            ('required_str_value', {'type': 'TypeError', 'msg': 'None is not an allow value',
                                    'validator': 'not_none_validator'}),
            ('required_bytes_value', {'type': 'TypeError', 'msg': 'None is not an allow value',
                                      'validator': 'not_none_validator'})
        ])


class RecursiveModel(BaseModel):
    grape: bool = ...
    banana: UltraSimpleModel = ...


def test_recursion():
    m = RecursiveModel(grape=1, banana={'a': 1})
    assert m.grape is True
    assert m.banana.a == 1.0
    assert m.banana.b == 10
    assert repr(m) == '<RecursiveModel grape=True banana=<UltraSimpleModel a=1.0 b=10>>'


def test_recursion_fails():
    with pytest.raises(ValidationError):
        RecursiveModel(grape=1, banana=123)


class PreventExtraModel(BaseModel):
    foo = 'whatever'

    class Config:
        allow_extra = False


def test_prevent_extra_success():
    m = PreventExtraModel()
    assert m.foo == 'whatever'
    m = PreventExtraModel(foo=1)
    assert m.foo == '1'


def test_prevent_extra_fails():
    with pytest.raises(ValidationError) as exc_info:
        PreventExtraModel(foo='ok', bar='wrong', spam='xx')
    assert exc_info.value.message == '1 error validating input'
    assert exc_info.value.pretty_errors == ('{"_extra": {"fields": ["bar", "spam"], '
                                            '"msg": "2 extra values in provided data", "type": "Extra"}}')


class InvalidValidator:
    @classmethod
    def get_validators(cls):
        yield cls.has_wrong_arguments

    @classmethod
    def has_wrong_arguments(cls, value, bar):
        pass


def test_invalid_validator():
    with pytest.raises(ConfigError) as exc_info:
        class InvalidValidatorModel(BaseModel):
            x: InvalidValidator = ...
    assert exc_info.value.args[0].startswith('Invalid signature for validator')


def test_no_validator():
    with pytest.raises(ConfigError) as exc_info:
        class NoValidatorModel(BaseModel):
            x: object = ...
    assert exc_info.value.args[0] == "no validator found for <class 'object'>"
