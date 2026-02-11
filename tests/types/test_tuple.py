import re
from dataclasses import dataclass

import pytest
from typing_extensions import Unpack

from pydantic import TypeAdapter, ValidationError


@dataclass
class Err:
    message: str


@pytest.mark.parametrize(
    ('input', 'expected'),
    [
        ((1,), (1,)),
        ([1, 'a'], (1, 'a')),
        ((1, 'a', 'b'), (1, 'a', 'b')),
        ([1, 'a', 'b', 'c'], (1, 'a', 'b', 'c')),
        (
            ('a', 'b'),
            Err(
                "1 validation error for tuple[int, str, ...]\n0\n  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]"
            ),
        ),
    ],
)
def test_tuple_prefix_variadic(input, expected):
    adapter = TypeAdapter(tuple[int, Unpack[tuple[str, ...]]])

    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            adapter.validate_python(input)
    else:
        assert adapter.validate_python(input) == expected


# def test_tuple_prefix_variadic_suffix():
#     adapter = TypeAdapter(tuple[int, Unpack[tuple[str, ...], int]])

#     class M(BaseModel):
#         x: tuple[int, str, *tuple[str, ...], int]

#     assert M(x=(1, 'a', 'b', 'c', 2)).x == (1, 'a', 'b', 'c', 2)


# def test_tuple_variadic_empty():
#     class M(BaseModel):
#         x: tuple[int, *tuple[str, ...]]

#     assert M(x=(1,)).x == (1,)


# TODO: add more tests for `Unpack` in tuple, non-variadic
