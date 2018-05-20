from typing import Dict, List, Union
from uuid import UUID

import pytest

from pydantic import BaseModel
from pydantic.exceptions import ValidationError, flatten_errors


class SubModel(BaseModel):
    x: int
    y: int
    z: str


class Model(BaseModel):
    a: int
    b: SubModel
    c: List[SubModel]
    d: Union[int, UUID]
    e: Dict[int, str]
    f: List[Union[int, str]]


def test_validation_error_display_errors():
    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj({
            'a': 'not_int',
            'b': {
                'y': 42,
            },
            'c': [
                {
                    'x': 'not_int',
                    'y': 42,
                    'z': 'string',
                },
            ],
            'd': 'string',
            'e': {
                'not_int': 'string',
            },
            'f': [
                None,
            ],
        })
    assert exc_info.value.display_errors == """a
  invalid literal for int() with base 10: 'not_int' (type=value_error)
b -> x
  field required (type=value_error.missing)
b -> z
  field required (type=value_error.missing)
c -> 0 -> x
  invalid literal for int() with base 10: 'not_int' (type=value_error)
d
  invalid literal for int() with base 10: 'string' (type=value_error)
d
  badly formed hexadecimal UUID string (type=value_error)
e -> __key__
  invalid literal for int() with base 10: 'not_int' (type=value_error)
f -> 0
  int() argument must be a string, a bytes-like object or a number, not 'NoneType' (type=type_error)
f -> 0
  None is not an allow value (type=type_error)"""


def test_validation_error_flat_errors():
    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj({
            'a': 'not_int',
            'b': {
                'y': 42,
            },
            'c': [
                {
                    'x': 'not_int',
                    'y': 42,
                    'z': 'string',
                },
            ],
            'd': 'string',
            'e': {
                'not_int': 'string',
            },
            'f': [
                None,
            ],
        })
    assert exc_info.value.flat_errors == [
        {
            'loc': (
                'a',
            ),
            'msg': 'invalid literal for int() with base 10: \'not_int\'',
            'type': 'value_error',
        },
        {
            'loc': (
                'b',
                'x',
            ),
            'msg': 'field required',
            'type': 'value_error.missing',
        },
        {
            'loc': (
                'b',
                'z',
            ),
            'msg': 'field required',
            'type': 'value_error.missing',
        },
        {
            'loc': (
                'c',
                '0',
                'x',
            ),
            'msg': 'invalid literal for int() with base 10: \'not_int\'',
            'type': 'value_error',
        },
        {
            'loc': (
                'd',
            ),
            'msg': 'invalid literal for int() with base 10: \'string\'',
            'type': 'value_error',
        },
        {
            'loc': (
                'd',
            ),
            'msg': 'badly formed hexadecimal UUID string',
            'type': 'value_error',
        },
        {
            'loc': (
                'e',
                '__key__',
            ),
            'msg': 'invalid literal for int() with base 10: \'not_int\'',
            'type': 'value_error',
        },
        {
            'loc': (
                'f',
                '0',
            ),
            'msg': 'int() argument must be a string, a bytes-like object or a number, not \'NoneType\'',
            'type': 'type_error',
        },
        {
            'loc': (
                'f',
                '0',
            ),
            'msg': 'None is not an allow value',
            'type': 'type_error',
        },
    ]


def test_validation_error_json():
    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj({
            'a': 'not_int',
            'b': {
                'y': 42,
            },
            'c': [
                {
                    'x': 'not_int',
                    'y': 42,
                    'z': 'string',
                },
            ],
            'd': 'string',
            'e': {
                'not_int': 'string',
            },
            'f': [
                None,
            ],
        })
    assert exc_info.value.json() == """[
  {
    "loc": [
      "a"
    ],
    "msg": "invalid literal for int() with base 10: 'not_int'",
    "type": "value_error"
  },
  {
    "loc": [
      "b",
      "x"
    ],
    "msg": "field required",
    "type": "value_error.missing"
  },
  {
    "loc": [
      "b",
      "z"
    ],
    "msg": "field required",
    "type": "value_error.missing"
  },
  {
    "loc": [
      "c",
      "0",
      "x"
    ],
    "msg": "invalid literal for int() with base 10: 'not_int'",
    "type": "value_error"
  },
  {
    "loc": [
      "d"
    ],
    "msg": "invalid literal for int() with base 10: 'string'",
    "type": "value_error"
  },
  {
    "loc": [
      "d"
    ],
    "msg": "badly formed hexadecimal UUID string",
    "type": "value_error"
  },
  {
    "loc": [
      "e",
      "__key__"
    ],
    "msg": "invalid literal for int() with base 10: 'not_int'",
    "type": "value_error"
  },
  {
    "loc": [
      "f",
      "0"
    ],
    "msg": "int() argument must be a string, a bytes-like object or a number, not 'NoneType'",
    "type": "type_error"
  },
  {
    "loc": [
      "f",
      "0"
    ],
    "msg": "None is not an allow value",
    "type": "type_error"
  }
]"""


def test_validation_error_str():
    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj({
            'a': 'not_int',
            'b': {
                'y': 42,
            },
            'c': [
                {
                    'x': 'not_int',
                    'y': 42,
                    'z': 'string',
                },
            ],
            'd': 'string',
            'e': {
                'not_int': 'string',
            },
            'f': [
                None,
            ],
        })
    assert str(exc_info.value) == """validation errors
a
  invalid literal for int() with base 10: 'not_int' (type=value_error)
b -> x
  field required (type=value_error.missing)
b -> z
  field required (type=value_error.missing)
c -> 0 -> x
  invalid literal for int() with base 10: 'not_int' (type=value_error)
d
  invalid literal for int() with base 10: 'string' (type=value_error)
d
  badly formed hexadecimal UUID string (type=value_error)
e -> __key__
  invalid literal for int() with base 10: 'not_int' (type=value_error)
f -> 0
  int() argument must be a string, a bytes-like object or a number, not 'NoneType' (type=type_error)
f -> 0
  None is not an allow value (type=type_error)"""


def test_flatten_errors_unknown_error_object():
    with pytest.raises(TypeError):
        flatten_errors([object])
