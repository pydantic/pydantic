from typing import List, Union

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
    assert """\
{
  "v": [
    {
      "error_msg": "None is not an allow value",
      "error_type": "TypeError",
      "index": null,
      "track": "str",
      "validator": "not_none_validator"
    },
    {
      "error_msg": "None is not an allow value",
      "error_type": "TypeError",
      "index": null,
      "track": "bytes",
      "validator": "not_none_validator"
    }
  ]
}""" == exc_info.value.json(2)


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
    assert """\
{
  "v": [
    {
      "error_msg": "int() argument must be a string, a bytes-like object or a number, not 'NoneType'",
      "error_type": "TypeError",
      "index": null,
      "track": "int",
      "validator": "int"
    },
    {
      "error_msg": "None is not an allow value",
      "error_type": "TypeError",
      "index": null,
      "track": "str",
      "validator": "not_none_validator"
    }
  ]
}""" == exc_info.value.json(2)


def test_typed_list():
    class Model(BaseModel):
        v: List[int] = ...

    m = Model(v=[1, 2, '3'])
    assert m.v == [1, 2, 3]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 'x', 'y'])
    assert exc_info.value.message == '1 error validating input'
    assert """\
{
  "v": [
    {
      "error_msg": "invalid literal for int() with base 10: 'x'",
      "error_type": "ValueError",
      "index": 1,
      "track": "int",
      "validator": "int"
    },
    {
      "error_msg": "invalid literal for int() with base 10: 'y'",
      "error_type": "ValueError",
      "index": 2,
      "track": "int",
      "validator": "int"
    }
  ]
}""" == exc_info.value.json(2)

    with pytest.raises(ValidationError) as exc_info:
        Model(v=1)
    assert exc_info.value.message == '1 error validating input'
    assert """\
{
  "v": {
    "error_msg": "'int' object is not iterable",
    "error_type": "TypeError",
    "index": null,
    "track": null,
    "validator": "iter"
  }
}""" == exc_info.value.json(2)
