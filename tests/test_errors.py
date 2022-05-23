import pickle
import sys
from typing import Dict, List, Optional, Union
from uuid import UUID, uuid4

import pytest
from typing_extensions import Literal

from pydantic import UUID1, BaseConfig, BaseModel, PydanticTypeError, ValidationError, conint, errors, validator
from pydantic.error_wrappers import flatten_errors, get_exc_type
from pydantic.errors import StrRegexError


def test_pydantic_error():
    class TestError(PydanticTypeError):
        code = 'test_code'
        msg_template = 'test message template "{test_ctx}"'

        def __init__(self, *, test_ctx: int) -> None:
            super().__init__(test_ctx=test_ctx)

    with pytest.raises(TestError) as exc_info:
        raise TestError(test_ctx='test_value')
    assert str(exc_info.value) == 'test message template "test_value"'


def test_pydantic_error_pickable():
    """
    Pydantic errors should be (un)pickable.
    (this test does not create a custom local error as we can't pickle local objects)
    """
    p = pickle.dumps(StrRegexError(pattern='pika'))
    error = pickle.loads(p)
    assert isinstance(error, StrRegexError)
    assert error.pattern == 'pika'


def test_interval_validation_error():
    class Foo(BaseModel):
        model_type: Literal['foo']
        f: int

    class Bar(BaseModel):
        model_type: Literal['bar']
        b: int

    class MyModel(BaseModel):
        foobar: Union[Foo, Bar]

        @validator('foobar', pre=True)
        def check_action(cls, v):
            if isinstance(v, dict):
                model_type = v.get('model_type')
                if model_type == 'foo':
                    return Foo(**v)
                if model_type == 'bar':
                    return Bar(**v)
            raise ValueError('not valid Foo or Bar')

    m1 = MyModel(foobar={'model_type': 'foo', 'f': '1'})
    assert m1.foobar.f == 1
    assert isinstance(m1.foobar, Foo)

    m2 = MyModel(foobar={'model_type': 'bar', 'b': '2'})
    assert m2.foobar.b == 2
    assert isinstance(m2.foobar, BaseModel)

    with pytest.raises(ValidationError) as exc_info:
        MyModel(foobar={'model_type': 'foo', 'f': 'x'})
    assert exc_info.value.errors() == [
        {'loc': ('foobar', 'f'), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


@pytest.mark.skipif(sys.version_info < (3, 7), reason='output slightly different for 3.6')
def test_error_on_optional():
    class Foobar(BaseModel):
        foo: Optional[str] = None

        @validator('foo', always=True, pre=True)
        def check_foo(cls, v):
            raise ValueError('custom error')

    with pytest.raises(ValidationError) as exc_info:
        Foobar(foo='x')
    assert exc_info.value.errors() == [{'loc': ('foo',), 'msg': 'custom error', 'type': 'value_error'}]
    assert repr(exc_info.value.raw_errors[0]) == "ErrorWrapper(exc=ValueError('custom error'), loc=('foo',))"

    with pytest.raises(ValidationError) as exc_info:
        Foobar(foo=None)
    assert exc_info.value.errors() == [{'loc': ('foo',), 'msg': 'custom error', 'type': 'value_error'}]


@pytest.mark.parametrize(
    'result,expected',
    (
        (
            'errors',
            [
                {'loc': ('a',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
                {'loc': ('b', 'x'), 'msg': 'field required', 'type': 'value_error.missing'},
                {'loc': ('b', 'z'), 'msg': 'field required', 'type': 'value_error.missing'},
                {'loc': ('c', 0, 'x'), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
                {'loc': ('d',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
                {'loc': ('d',), 'msg': 'value is not a valid uuid', 'type': 'type_error.uuid'},
                {'loc': ('e', '__key__'), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
                {'loc': ('f', 0), 'msg': 'none is not an allowed value', 'type': 'type_error.none.not_allowed'},
                {
                    'loc': ('g',),
                    'msg': 'uuid version 1 expected',
                    'type': 'value_error.uuid.version',
                    'ctx': {'required_version': 1},
                },
                {
                    'loc': ('h',),
                    'msg': 'yet another error message template 42',
                    'type': 'value_error.number.not_gt',
                    'ctx': {'limit_value': 42},
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
    "msg": "none is not an allowed value",
    "type": "type_error.none.not_allowed"
  },
  {
    "loc": [
      "g"
    ],
    "msg": "uuid version 1 expected",
    "type": "value_error.uuid.version",
    "ctx": {
      "required_version": 1
    }
  },
  {
    "loc": [
      "h"
    ],
    "msg": "yet another error message template 42",
    "type": "value_error.number.not_gt",
    "ctx": {
      "limit_value": 42
    }
  }
]""",
        ),
        (
            '__str__',
            """\
10 validation errors for Model
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
  none is not an allowed value (type=type_error.none.not_allowed)
g
  uuid version 1 expected (type=value_error.uuid.version; required_version=1)
h
  yet another error message template 42 (type=value_error.number.not_gt; limit_value=42)""",
        ),
    ),
)
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
            error_msg_templates = {'value_error.number.not_gt': 'yet another error message template {limit_value}'}

    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj(
            {
                'a': 'not_int',
                'b': {'y': 42},
                'c': [{'x': 'not_int', 'y': 42, 'z': 'string'}],
                'd': 'string',
                'e': {'not_int': 'string'},
                'f': [None],
                'g': uuid4(),
                'h': 21,
            }
        )

    assert getattr(exc_info.value, result)() == expected


def test_errors_unknown_error_object():
    with pytest.raises(RuntimeError):
        list(flatten_errors([object], BaseConfig))


@pytest.mark.parametrize(
    'exc,type_',
    (
        (TypeError(), 'type_error'),
        (ValueError(), 'value_error'),
        (AssertionError(), 'assertion_error'),
        (errors.DecimalIsNotFiniteError(), 'value_error.decimal.not_finite'),
    ),
)
def test_get_exc_type(exc, type_):
    if isinstance(type_, str):
        assert get_exc_type(type(exc)) == type_
    else:
        with pytest.raises(type_) as exc_info:
            get_exc_type(type(exc))
        assert isinstance(exc_info.value, type_)


def test_single_error():
    class Model(BaseModel):
        x: int

    with pytest.raises(ValidationError) as exc_info:
        Model(x='x')

    expected = """\
1 validation error for Model
x
  value is not a valid integer (type=type_error.integer)"""
    assert str(exc_info.value) == expected
    assert str(exc_info.value) == expected  # to check lru cache doesn't break anything

    with pytest.raises(ValidationError) as exc_info:
        Model()

    assert (
        str(exc_info.value)
        == """\
1 validation error for Model
x
  field required (type=value_error.missing)"""
    )


def test_nested_error():
    class NestedModel3(BaseModel):
        x: str

    class NestedModel2(BaseModel):
        data2: List[NestedModel3]

    class NestedModel1(BaseModel):
        data1: List[NestedModel2]

    with pytest.raises(ValidationError) as exc_info:
        NestedModel1(data1=[{'data2': [{'y': 1}]}])

    expected = [{'loc': ('data1', 0, 'data2', 0, 'x'), 'msg': 'field required', 'type': 'value_error.missing'}]

    assert exc_info.value.errors() == expected


def test_validate_assignment_error():
    class Model(BaseModel):
        x: int

        class Config:
            validate_assignment = True

    model = Model(x=1)
    with pytest.raises(ValidationError) as exc_info:
        model.x = 'a'
    assert (
        str(exc_info.value)
        == '1 validation error for Model\nx\n  value is not a valid integer (type=type_error.integer)'
    )


def test_submodel_override_validation_error():
    class SubmodelA(BaseModel):
        x: str

    class SubmodelB(SubmodelA):
        x: int

    class Model(BaseModel):
        submodel: SubmodelB

    submodel = SubmodelA(x='a')
    with pytest.raises(ValidationError) as exc_info:
        Model(submodel=submodel)
    assert exc_info.value.errors() == [
        {'loc': ('submodel', 'x'), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}
    ]


def test_validation_error_methods():
    class Model(BaseModel):
        x: int

    with pytest.raises(ValidationError) as exc_info:
        Model(x='x')
    e = exc_info.value
    assert (
        str(e)
        == """\
1 validation error for Model
x
  value is not a valid integer (type=type_error.integer)"""
    )
    assert e.errors() == [{'loc': ('x',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}]
    assert e.json(indent=None) == (
        '[{"loc": ["x"], "msg": "value is not a valid integer", "type": "type_error.integer"}]'
    )
    assert repr(e) == (
        "ValidationError(model='Model', errors=[{'loc': ('x',), 'msg': 'value is not a valid integer', "
        "'type': 'type_error.integer'}])"
    )
