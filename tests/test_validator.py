from typing import Any, Dict, ForwardRef, List, NamedTuple, Tuple

import pytest
from typing_extensions import TypedDict

from pydantic import BaseModel, Validator


class PydanticModel(BaseModel):
    x: int


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
        (int | str, 1, 1),
        (int | str, '2', '2'),
    ],
)
def test_types(tp: Any, val: Any, expected: Any):
    v = Validator(tp)
    assert expected == v(val)


def test_local_namespace_variables():
    IntList = List[int]
    OuterDict = Dict[str, 'IntList']

    v = Validator(OuterDict)

    res = v({'foo': [1, '2']})
    assert res == {'foo': [1, 2]}


def test_top_level_fwd_ref():
    IntList = List[int]
    OuterDict = Dict[str, 'IntList']
    FwdRef = ForwardRef('Dict[str, List[int]]', module=__name__)

    v: Validator[OuterDict] = Validator(FwdRef)

    res = v({'foo': [1, '2']})
    assert res == {'foo': [1, 2]}
