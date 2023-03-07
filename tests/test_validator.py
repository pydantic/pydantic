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
    'tp, val',
    [
        (PydanticModel, PydanticModel(x=1)),
        (PydanticModel, {'x': 1}),
        (ATypedDict, ATypedDict(x=1)),
        (ATypedDict, dict(x=1)),
        (ANamedTuple, ANamedTuple(x=1)),
        (List[str], ['1', '2']),
        (Tuple[str], ('1',)),
        (Tuple[str, int], ('1', 1)),
        (Tuple[str, ...], ('1',)),
        (Dict[str, int], {'foo': 123}),
        (int | str, 1),
        (int | str, '2'),
    ],
)
def test_list(tp: Any, val: Any):
    v = Validator(tp)
    assert val == v(val)
