import json
import sys
from typing import Any, Dict, ForwardRef, Generic, List, NamedTuple, Tuple, TypeVar, Union

import pytest
from pydantic_core import ValidationError
from typing_extensions import TypeAlias, TypedDict

from pydantic import BaseModel, TypeAdapter, ValidationInfo, field_validator
from pydantic.config import ConfigDict

ItemType = TypeVar('ItemType')

NestedList = List[List[ItemType]]


class PydanticModel(BaseModel):
    x: int


T = TypeVar('T')


class GenericPydanticModel(BaseModel, Generic[T]):
    x: NestedList[T]


class SomeTypedDict(TypedDict):
    x: int


class SomeNamedTuple(NamedTuple):
    x: int


@pytest.mark.parametrize(
    'tp, val, expected',
    [
        (PydanticModel, PydanticModel(x=1), PydanticModel(x=1)),
        (PydanticModel, {'x': 1}, PydanticModel(x=1)),
        (SomeTypedDict, {'x': 1}, {'x': 1}),
        (SomeNamedTuple, SomeNamedTuple(x=1), SomeNamedTuple(x=1)),
        (List[str], ['1', '2'], ['1', '2']),
        (Tuple[str], ('1',), ('1',)),
        (Tuple[str, int], ('1', 1), ('1', 1)),
        (Tuple[str, ...], ('1',), ('1',)),
        (Dict[str, int], {'foo': 123}, {'foo': 123}),
        (Union[int, str], 1, 1),
        (Union[int, str], '2', '2'),
        (GenericPydanticModel[int], {'x': [[1]]}, GenericPydanticModel[int](x=[[1]])),
        (GenericPydanticModel[int], {'x': [['1']]}, GenericPydanticModel[int](x=[[1]])),
        (NestedList[int], [[1]], [[1]]),
        (NestedList[int], [['1']], [[1]]),
    ],
)
def test_types(tp: Any, val: Any, expected: Any):
    v = TypeAdapter(tp).validate_python
    assert expected == v(val)


IntList = List[int]
OuterDict = Dict[str, 'IntList']


def test_global_namespace_variables():
    v = TypeAdapter(OuterDict).validate_python
    res = v({'foo': [1, '2']})
    assert res == {'foo': [1, 2]}


def test_local_namespace_variables():
    IntList = List[int]
    OuterDict = Dict[str, 'IntList']

    v = TypeAdapter(OuterDict).validate_python

    res = v({'foo': [1, '2']})
    assert res == {'foo': [1, 2]}


@pytest.mark.skipif(sys.version_info < (3, 9), reason="ForwardRef doesn't accept module as a parameter in Python < 3.9")
def test_top_level_fwd_ref():
    FwdRef = ForwardRef('OuterDict', module=__name__)
    v = TypeAdapter(FwdRef).validate_python

    res = v({'foo': [1, '2']})
    assert res == {'foo': [1, 2]}


MyUnion: TypeAlias = 'Union[str, int]'


def test_type_alias():
    MyList = List[MyUnion]
    v = TypeAdapter(MyList).validate_python
    res = v([1, '2'])
    assert res == [1, '2']


def test_validate_python_strict() -> None:
    class Model(TypedDict):
        x: int

    lax_validator = TypeAdapter(Model, config=ConfigDict(strict=False))
    strict_validator = TypeAdapter(Model, config=ConfigDict(strict=True))

    assert lax_validator.validate_python({'x': '1'}, strict=None) == Model(x=1)
    assert lax_validator.validate_python({'x': '1'}, strict=False) == Model(x=1)
    with pytest.raises(ValidationError) as exc_info:
        lax_validator.validate_python({'x': '1'}, strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        strict_validator.validate_python({'x': '1'})
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]
    assert strict_validator.validate_python({'x': '1'}, strict=False) == Model(x=1)
    with pytest.raises(ValidationError) as exc_info:
        strict_validator.validate_python({'x': '1'}, strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]


def test_validate_json_strict() -> None:
    class Model(TypedDict):
        x: int

    lax_validator = TypeAdapter(Model, config=ConfigDict(strict=False))
    strict_validator = TypeAdapter(Model, config=ConfigDict(strict=True))

    assert lax_validator.validate_json(json.dumps({'x': '1'}), strict=None) == Model(x=1)
    assert lax_validator.validate_json(json.dumps({'x': '1'}), strict=False) == Model(x=1)
    with pytest.raises(ValidationError) as exc_info:
        lax_validator.validate_json(json.dumps({'x': '1'}), strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        strict_validator.validate_json(json.dumps({'x': '1'}), strict=None)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]
    assert strict_validator.validate_json(json.dumps({'x': '1'}), strict=False) == Model(x=1)
    with pytest.raises(ValidationError) as exc_info:
        strict_validator.validate_json(json.dumps({'x': '1'}), strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('x',), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]


def test_validate_python_context() -> None:
    contexts: List[Any] = [None, None, {'foo': 'bar'}]

    class Model(BaseModel):
        x: int

        @field_validator('x')
        def val_x(cls, v: int, info: ValidationInfo) -> int:
            assert info.context == contexts.pop(0)
            return v

    validator = TypeAdapter(Model)
    validator.validate_python({'x': 1})
    validator.validate_python({'x': 1}, context=None)
    validator.validate_python({'x': 1}, context={'foo': 'bar'})
    assert contexts == []


def test_validate_json_context() -> None:
    contexts: List[Any] = [None, None, {'foo': 'bar'}]

    class Model(BaseModel):
        x: int

        @field_validator('x')
        def val_x(cls, v: int, info: ValidationInfo) -> int:
            assert info.context == contexts.pop(0)
            return v

    validator = TypeAdapter(Model)
    validator.validate_json(json.dumps({'x': 1}))
    validator.validate_json(json.dumps({'x': 1}), context=None)
    validator.validate_json(json.dumps({'x': 1}), context={'foo': 'bar'})
    assert contexts == []


def test_merge_config() -> None:
    class Model(BaseModel):
        x: int
        y: str

        model_config = ConfigDict(strict=True, title='FooModel')

    adapted = TypeAdapter(Model, config=ConfigDict(strict=False, str_max_length=20))

    # strict=False gets applied to the outer Model but not to the inner typeddict validator
    # so we're allowed to validate a dict but `x` still must be an int
    adapted.validate_python({'x': 1, 'y': '2'})
    assert adapted.json_schema()['title'] == 'FooModel'
    with pytest.raises(ValidationError) as exc_info:
        adapted.validate_python({'x': 1, 'y': 'x' * 21})
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_too_long',
            'loc': ('y',),
            'msg': 'String should have at most 20 characters',
            'input': 'xxxxxxxxxxxxxxxxxxxxx',
            'ctx': {'max_length': 20},
        }
    ]
