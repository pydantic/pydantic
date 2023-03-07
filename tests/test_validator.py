from typing import Any, Dict, List, NamedTuple, Tuple

import pytest
from typing_extensions import TypedDict

from pydantic.main import BaseModel
from pydantic.validator import Validator


class PydanticModel(BaseModel):
    x: int


class ATypedDict(TypedDict):
    x: int


class ANamedTuple(NamedTuple):
    x: int


@pytest.mark.parametrize(
    'tp, val, expected',
    [
        (PydanticModel, PydanticModel(x=1), PydanticModel(x=1)),
        (PydanticModel, {'x': 1}, PydanticModel(x=1)),
        (ATypedDict, {'x': 1}, {'x': 1}),
        (ANamedTuple, ANamedTuple(x=1), ANamedTuple(x=1)),
        (List[str], ['1', '2'], ['1', '2']),
        (Tuple[str], ('1',), ('1',)),
        (Tuple[str, int], ('1', 1), ('1', 1)),
        (Tuple[str, ...], ('1',), ('1',)),
        (Dict[str, int], {'foo': 123}, {'foo': 123}),
        (int | str, 1, 1),
        (int | str, '2', '2'),
    ],
)
def test_ok(tp: Any, val: Any, expected: Any):
    v = Validator(tp)
    assert expected == v(val)
