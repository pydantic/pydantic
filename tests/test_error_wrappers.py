from typing import Dict, List, Union
from uuid import UUID, uuid4

import pytest

from pydantic import UUID1, BaseModel, conint, errors
from pydantic.error_wrappers import ValidationError, flatten_errors, get_exc_type


@pytest.mark.parametrize('result,expected', (
    (
        'display_errors',
        """\
a
  value is not a valid integer (type=type_error.integer)
b -> x
  field required (type=value_error.missing)
b -> z
  field required (type=value_error.missing)
c -> 0 -> x
  value is not a valid integer (type=type_error.integer)
d
  value is not a valid integer (type=type_error.integer)
d
  value is not a valid uuid (type=type_error.uuid)
e -> __key__
  value is not a valid integer (type=type_error.integer)
f -> 0
  value is not a valid integer (type=type_error.integer)
f -> 0
  none is not an allow value (type=type_error.none.not_allowed)
g
  uuid version 1 expected (type=value_error.uuid.version; required_version=1)
h
  yet another error message template 42 (type=value_error.number.not_gt; limit_value=42)""",
    ),
    (
        'flatten_errors',
        [
            {
                'loc': (
                    'a',
                ),
                'msg': 'value is not a valid integer',
                'type': 'type_error.integer',
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
                'msg': 'value is not a valid integer',
                'type': 'type_error.integer',
            },
            {
                'loc': (
                    'd',
                ),
                'msg': 'value is not a valid integer',
                'type': 'type_error.integer',
            },
            {
                'loc': (
                    'd',
                ),
                'msg': 'value is not a valid uuid',
                'type': 'type_error.uuid',
            },
            {
                'loc': (
                    'e',
                    '__key__',
                ),
                'msg': 'value is not a valid integer',
                'type': 'type_error.integer',
            },
            {
                'loc': (
                    'f',
                    0,
                ),
                'msg': 'value is not a valid integer',
                'type': 'type_error.integer',
            },
            {
                'loc': (
                    'f',
                    0,
                ),
                'msg': 'none is not an allow value',
                'type': 'type_error.none.not_allowed',
            },
            {
                'loc': (
                    'g',
                ),
                'msg': 'uuid version 1 expected',
                'type': 'value_error.uuid.version',
                'ctx': {
                    'required_version': 1,
                },
            },
            {
                'loc': (
                    'h',
                ),
                'msg': 'yet another error message template 42',
                'type': 'value_error.number.not_gt',
                'ctx': {
                    'limit_value': 42,
                },
            }
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
    "msg": "value is not a valid integer",
    "type": "type_error.integer"
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
    "msg": "value is not a valid integer",
    "type": "type_error.integer"
  },
  {
    "loc": [
      "d"
    ],
    "msg": "value is not a valid integer",
    "type": "type_error.integer"
  },
  {
    "loc": [
      "d"
    ],
    "msg": "value is not a valid uuid",
    "type": "type_error.uuid"
  },
  {
    "loc": [
      "e",
      "__key__"
    ],
    "msg": "value is not a valid integer",
    "type": "type_error.integer"
  },
  {
    "loc": [
      "f",
      0
    ],
    "msg": "value is not a valid integer",
    "type": "type_error.integer"
  },
  {
    "loc": [
      "f",
      0
    ],
    "msg": "none is not an allow value",
    "type": "type_error.none.not_allowed"
  },
  {
    "ctx": {
      "required_version": 1
    },
    "loc": [
      "g"
    ],
    "msg": "uuid version 1 expected",
    "type": "value_error.uuid.version"
  },
  {
    "ctx": {
      "limit_value": 42
    },
    "loc": [
      "h"
    ],
    "msg": "yet another error message template 42",
    "type": "value_error.number.not_gt"
  }
]"""
    ),
    (
        '__str__',
        """\
validation errors
a
  value is not a valid integer (type=type_error.integer)
b -> x
  field required (type=value_error.missing)
b -> z
  field required (type=value_error.missing)
c -> 0 -> x
  value is not a valid integer (type=type_error.integer)
d
  value is not a valid integer (type=type_error.integer)
d
  value is not a valid uuid (type=type_error.uuid)
e -> __key__
  value is not a valid integer (type=type_error.integer)
f -> 0
  value is not a valid integer (type=type_error.integer)
f -> 0
  none is not an allow value (type=type_error.none.not_allowed)
g
  uuid version 1 expected (type=value_error.uuid.version; required_version=1)
h
  yet another error message template 42 (type=value_error.number.not_gt; limit_value=42)"""
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
        g: UUID1
        h: conint(gt=42)

        class Config:
            error_msg_templates = {
                'value_error.number.not_gt': 'yet another error message template {limit_value}',
            }

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
            'g': uuid4(),
            'h': 21,
        })

    result = getattr(exc_info.value, result)
    if callable(result):
        result = result()

    assert result == expected


def test_flatten_errors_unknown_error_object():
    with pytest.raises(RuntimeError):
        list(flatten_errors([object]))


@pytest.mark.parametrize('exc,type_', (
    (TypeError(), 'type_error'),
    (ValueError(), 'value_error'),
    (errors.DecimalIsNotFiniteError(), 'value_error.decimal.not_finite'),
))
def test_get_exc_type(exc, type_):
    if isinstance(type_, str):
        assert get_exc_type(exc) == type_
    else:
        with pytest.raises(type_) as exc_info:
            get_exc_type(exc)
        assert isinstance(exc_info.value, type_)
