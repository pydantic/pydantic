from enum import Enum
from typing import Dict, List, Union

import pytest

from pydantic import BaseModel, NoneStrBytes, StrBytes, ValidationError


def test_str_bytes():
    class StrBytesModel(BaseModel):
        v: StrBytes = ...

    m = StrBytesModel(v='s')
    assert m.v == 's'
    assert ("<Field v: "
            "type='typing.Union[str, bytes]', "
            "required=True, "
            "sub_fields=["
            "<Field v_str: type='str', required=True, validators=['not_none_validator', 'str_validator', "
            "'anystr_length_validator']>, "
            "<Field v_bytes: type='bytes', required=True, validators=['not_none_validator', 'bytes_validator', "
            "'anystr_length_validator']>]>") == repr(m.fields['v'])

    m = StrBytesModel(v=b'b')
    assert m.v == 'b'

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
      "track": "str"
    },
    {
      "error_msg": "None is not an allow value",
      "error_type": "TypeError",
      "index": null,
      "track": "bytes"
    }
  ]
}""" == exc_info.value.json(2)


def test_str_bytes_none():
    class StrBytesModel(BaseModel):
        v: NoneStrBytes = ...

    m = StrBytesModel(v='s')
    assert m.v == 's'

    m = StrBytesModel(v=b'b')
    assert m.v == 'b'

    m = StrBytesModel(v=None)
    assert m.v is None

    # NOTE not_none_validator removed
    assert ("OrderedDict(["
            "('type', 'typing.Union[str, bytes, NoneType]'), "
            "('required', True), "
            "('sub_fields', ["
            "<Field v_str: type='str', required=True, validators=['str_validator', 'anystr_length_validator']>, "
            "<Field v_bytes: type='bytes', required=True, validators=['bytes_validator', 'anystr_length_validator']>"
            "])])") == repr(m.fields['v'].info)


def test_union_int_str():
    class Model(BaseModel):
        v: Union[int, str] = ...

    m = Model(v=123)
    assert m.v == 123

    m = Model(v='123')
    assert m.v == 123

    m = Model(v=b'foobar')
    assert m.v == 'foobar'

    # here both validators work and it's impossible to work out which value "closer"
    m = Model(v=12.2)
    assert m.v == 12

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
      "track": "int"
    },
    {
      "error_msg": "None is not an allow value",
      "error_type": "TypeError",
      "index": null,
      "track": "str"
    }
  ]
}""" == exc_info.value.json(2)


def test_union_priority():
    class ModelOne(BaseModel):
        v: Union[int, str] = ...

    class ModelTwo(BaseModel):
        v: Union[str, int] = ...

    assert ModelOne(v='123').v == 123
    assert ModelTwo(v='123').v == '123'


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
      "track": "int"
    },
    {
      "error_msg": "invalid literal for int() with base 10: 'y'",
      "error_type": "ValueError",
      "index": 2,
      "track": "int"
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
    "track": null
  }
}""" == exc_info.value.json(2)


class DictModel(BaseModel):
    v: Dict[str, int] = ...


@pytest.mark.parametrize('value,result', [
    ({'a': 2, 'b': 4}, {'a': 2, 'b': 4}),
    ({1: '2', 'b': 4}, {'1': 2, 'b': 4}),
    ([('a', 2), ('b', 4)], {'a': 2, 'b': 4}),
])
def test_typed_dict(value, result):
    assert DictModel(v=value).v == result


@pytest.mark.parametrize('value,error', [
    (
        1,
        """\
1 error validating input
v:
  'int' object is not iterable (error_type=TypeError)"""
    ),
    (
        {'a': 'b'},
        """\
1 error validating input
v:
  invalid literal for int() with base 10: 'b' (error_type=ValueError track=int index=a)"""
    ),
    (
        [1, 2, 3],
        """\
1 error validating input
v:
  cannot convert dictionary update sequence element #0 to a sequence (error_type=TypeError)""",
    )
])
def test_typed_dict_error(value, error):
    with pytest.raises(ValidationError) as exc_info:
        DictModel(v=value)
    assert error == str(exc_info.value)


def test_dict_key_error():
    class DictIntModel(BaseModel):
        v: Dict[int, int] = ...
    assert DictIntModel(v={1: 2, '3': '4'}).v == {1: 2, 3: 4}
    with pytest.raises(ValidationError) as exc_info:
        DictIntModel(v={'foo': 2, '3': '4'})
    assert """\
1 error validating input
v:
  invalid literal for int() with base 10: 'foo' (error_type=ValueError track=int index=key)""" == str(exc_info.value)


def test_all_model_validator():
    class OverModel(BaseModel):
        a: int = ...

        def validate_a_pre(self, v):
            return f'{v}1'

        def validate_a(self, v):
            assert isinstance(v, int)
            return f'{v}_main'

        def validate_a_post(self, v):
            assert isinstance(v, str)
            return f'{v}_post'

    m = OverModel(a=1)
    assert m.a == '11_main_post'


def test_recursive_list():
    class SubModel(BaseModel):
        name: str = ...
        count: int = None

    class Model(BaseModel):
        v: List[SubModel] = []

    m = Model(v=[])
    assert m.v == []

    m = Model(v=[{'name': 'testing', 'count': 4}])
    assert "<Model v=[<SubModel name='testing' count=4>]>" == repr(m)
    assert m.v[0].name == 'testing'
    assert m.v[0].count == 4

    with pytest.raises(ValidationError) as exc_info:
        Model(v=['x'])
    print(exc_info.value.json())
    assert 'dictionary update sequence element #0 has length 1; 2 is required' in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[{}])

    assert """\
1 error validating input
v:
  1 error validating input (error_type=ValidationError track=SubModel)
    name:
      field required (error_type=Missing)\
""" == str(exc_info.value)
    assert """\
{
  "v": [
    {
      "error_details": {
        "name": {
          "error_msg": "field required",
          "error_type": "Missing",
          "index": null,
          "track": null
        }
      },
      "error_msg": "1 error validating input",
      "error_type": "ValidationError",
      "index": 0,
      "track": "SubModel"
    }
  ]
}""" == exc_info.value.json(2)


def test_list_unions():
    class Model(BaseModel):
        v: List[Union[int, str]] = ...

    assert Model(v=[123, '456', 'foobar']).v == [123, 456, 'foobar']

    with pytest.raises(ValidationError) as exc_info:
        Model(v=[1, 2, None])
    assert """\
1 error validating input
v:
  int() argument must be a string, a bytes-like object or a number, not 'NoneType' \
(error_type=TypeError track=int index=2)
  None is not an allow value (error_type=TypeError track=str index=2)\
""" == str(exc_info.value)


def test_recursive_lists():
    class Model(BaseModel):
        v: List[List[Union[int, float]]] = ...

    assert Model(v=[[1, 2], [3, '4', '4.1']]).v == [[1, 2], [3, 4, 4.1]]
    assert Model.__fields__['v'].sub_fields[0].name == '_v'
    assert len(Model.__fields__['v'].sub_fields) == 1
    assert Model.__fields__['v'].sub_fields[0].sub_fields[0].name == '__v'
    assert len(Model.__fields__['v'].sub_fields[0].sub_fields) == 1
    assert Model.__fields__['v'].sub_fields[0].sub_fields[0].sub_fields[1].name == '__v_float'
    assert len(Model.__fields__['v'].sub_fields[0].sub_fields[0].sub_fields) == 2


def test_str_enum():
    class StrEnum(str, Enum):
        a = 'a10'
        b = 'b10'

    class Model(BaseModel):
        v: StrEnum = ...

    assert Model(v='a10').v is StrEnum.a

    with pytest.raises(ValidationError):
        Model(v='different')
