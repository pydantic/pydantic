from typing import Dict, List, Union
from uuid import UUID

import pytest

from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError, flatten_errors


@pytest.mark.parametrize('result,expected', (
    (
        'display_errors',
        """\
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
  None is not an allow value (type=type_error)""",
    ),
    (
        'flatten_errors',
        [
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
                    0,
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
                    0,
                ),
                'msg': 'int() argument must be a string, a bytes-like object or a number, not \'NoneType\'',
                'type': 'type_error',
            },
            {
                'loc': (
                    'f',
                    0,
                ),
                'msg': 'None is not an allow value',
                'type': 'type_error',
            },
        ],
    ),
    (
        'json',
        """\
[
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
      0,
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
      0
    ],
    "msg": "int() argument must be a string, a bytes-like object or a number, not 'NoneType'",
    "type": "type_error"
  },
  {
    "loc": [
      "f",
      0
    ],
    "msg": "None is not an allow value",
    "type": "type_error"
  }
]"""
    ),
    (
        '__str__',
        """\
validation errors
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
    ),
))
def test_validation_error(result, expected):
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

    result = getattr(exc_info.value, result)
    if callable(result):
        result = result()

    assert result == expected


def test_flatten_errors_unknown_error_object():
    with pytest.raises(RuntimeError):
        list(flatten_errors([object]))
