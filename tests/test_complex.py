from collections import OrderedDict
from typing import Union

import pytest

from pydantic import BaseModel, NoneStrBytes, StrBytes, ValidationError


def test_str_bytes():
    class StrBytesModel(BaseModel):
        v: StrBytes = ...

    m = StrBytesModel(v='s')
    assert m.v == 's'
    assert repr(m.fields['v']) == (
        "<Field v: type='typing.Union[str, bytes]', required=True, "
        "validators={'str': ['not_none_validator', 'str_validator', 'anystr_length_validator'], "
        "'bytes': ['not_none_validator', 'bytes_validator', 'anystr_length_validator']}>"
    )

    m = StrBytesModel(v=b'b')
    assert m.v == b'b'

    with pytest.raises(ValidationError) as exc_info:
        StrBytesModel(v=None)
    assert exc_info.value.message == '1 error validating input'
    assert exc_info.value.errors == OrderedDict(
        [
            ('v', [{'type': 'TypeError', 'route': 'str', 'msg': 'None is not an allow value',
                    'validator': 'not_none_validator'},
                   {'type': 'TypeError', 'route': 'bytes', 'msg': 'None is not an allow value',
                    'validator': 'not_none_validator'}])
        ])


def test_str_bytes_none():
    class StrBytesModel(BaseModel):
        v: NoneStrBytes = ...

    m = StrBytesModel(v='s')
    assert m.v == 's'

    m = StrBytesModel(v=b'b')
    assert m.v == b'b'

    m = StrBytesModel(v=None)
    assert m.v is None

    assert m.fields['v'].info == {
        'required': True,
        'type': 'typing.Union[str, bytes, NoneType]',
        'validators': {
            'bytes': ['bytes_validator', 'anystr_length_validator'],
            'str': ['str_validator', 'anystr_length_validator']
        }
    }


def test_union_int_str():
    class Model(BaseModel):
        v: Union[int, str] = ...

    m = Model(v=123)
    assert m.v == 123

    m = Model(v='123')
    assert m.v == '123'

    m = Model(v=b'foobar')
    assert m.v == 'foobar'

    # here both validators work and it's impossible to work out which value "closer"
    m = Model(v=12.2)
    assert m.v == '12.2'

    with pytest.raises(ValidationError) as exc_info:
        Model(v=None)
    assert exc_info.value.message == '1 error validating input'
    assert exc_info.value.errors == OrderedDict(
        [
            ('v', [{'type': 'TypeError', 'route': 'int', 'validator': 'int',
                    'msg': "int() argument must be a string, a bytes-like object or a number, not 'NoneType'"},
                   {'type': 'TypeError', 'route': 'str', 'msg': 'None is not an allow value',
                    'validator': 'not_none_validator'}])
        ])
