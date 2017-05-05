from collections import OrderedDict

import pytest

from pydantic import DSN, BaseModel, NoneBytes, NoneStr, ValidationError


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
    assert exc_info.value.args[0] == ('1 errors validating input: {"a": {"msg": "field required", '
                                      '"type": "Missing", "validator": "field_required"}}')


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


class ConfigModel(UltraSimpleModel):
    class Config:
        raise_exception = False


def test_config_doesnt_raise():
    m = ConfigModel()
    assert m.errors == OrderedDict([('a', {'type': 'Missing', 'msg': 'field required', "validator": "field_required"})])
    assert m.config.raise_exception is False
    assert m.config.max_anystr_length == 65536


class DsnModel(BaseModel):
    db_name = 'foobar'
    db_user = 'postgres'
    db_password: str = None
    db_host = 'localhost'
    db_port = '5432'
    db_driver = 'postgres'
    dsn: DSN = None


def test_dsn_compute():
    m = DsnModel()
    assert m.dsn == 'postgres://postgres@localhost:5432/foobar'


def test_dsn_define():
    m = DsnModel(dsn='postgres://postgres@localhost:5432/different')
    assert m.dsn == 'postgres://postgres@localhost:5432/different'


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
