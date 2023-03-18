import sys
from typing import Any, ForwardRef, Generic, NamedTuple, TypeAlias, TypeVar, Union

import pytest
from typing_extensions import TypedDict

from pydantic import BaseModel, Validator

ItemType = TypeVar('ItemType')

NestedList = list[list[ItemType]]


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
        (list[str], ['1', '2'], ['1', '2']),
        (tuple[str], ('1',), ('1',)),
        (tuple[str, int], ('1', 1), ('1', 1)),
        (tuple[str, ...], ('1',), ('1',)),
        (dict[str, int], {'foo': 123}, {'foo': 123}),
        (Union[int, str], 1, 1),
        (Union[int, str], '2', '2'),
        (GenericPydanticModel[int], {'x': [[1]]}, GenericPydanticModel[int](x=[[1]])),
        (GenericPydanticModel[int], {'x': [['1']]}, GenericPydanticModel[int](x=[[1]])),
        (NestedList[int], [[1]], [[1]]),
        (NestedList[int], [['1']], [[1]]),
    ],
)
def test_types(tp: Any, val: Any, expected: Any):
    v = Validator(tp)
    assert expected == v(val)


IntList = list[int]
OuterDict = dict[str, 'IntList']


def test_global_namespace_variables():
    v = Validator(OuterDict)
    res = v({'foo': [1, '2']})
    assert res == {'foo': [1, 2]}


def test_local_namespace_variables():
    IntList = list[int]
    OuterDict = dict[str, 'IntList']

    v = Validator(OuterDict)

    res = v({'foo': [1, '2']})
    assert res == {'foo': [1, 2]}


@pytest.mark.skipif(sys.version_info < (3, 9), reason="ForwardRef doesn't accept module as a parameter in Python < 3.9")
def test_top_level_fwd_ref():
    FwdRef = ForwardRef('OuterDict', module=__name__)
    v: Validator[OuterDict] = Validator(FwdRef)

    res = v({'foo': [1, '2']})
    assert res == {'foo': [1, 2]}


MyUnion: TypeAlias = 'Union[str, int]'


def test_type_alias():
    MyList = list[MyUnion]
    v: Validator[MyList] = Validator(MyList)
    res = v([1, '2'])
    assert res == [1, '2']
