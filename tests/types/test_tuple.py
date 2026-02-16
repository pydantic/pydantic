import re
from dataclasses import dataclass

import pytest
from typing_extensions import Unpack

from pydantic import TypeAdapter, ValidationError


@dataclass
class Err:
    message: str
    exception_type: type[BaseException] = ValidationError


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
        with pytest.raises(expected.exception_type, match=re.escape(expected.message)):
            adapter.validate_python(input)
    else:
        assert adapter.validate_python(input) == expected


@pytest.mark.parametrize(
    ('input', 'expected'),
    [
        ((), Err('type=missing')),
        ((1,), Err('type=missing')),
        ((1, 2), (1, 2)),
        ([1, 'a', 2], (1, 'a', 2)),
        ((1, 'a', 'b', 2), (1, 'a', 'b', 2)),
        ([1, 'a', 'b', 'c', 2], (1, 'a', 'b', 'c', 2)),
        (
            ('a', 'b'),
            Err('2 validation errors for tuple[int, str, ..., int]'),
        ),
    ],
)
def test_tuple_prefix_variadic_suffix(input, expected):
    adapter = TypeAdapter(tuple[int, Unpack[tuple[str, ...]], int])

    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            adapter.validate_python(input)
    else:
        assert adapter.validate_python(input) == expected


@pytest.mark.parametrize(
    ('input', 'expected'),
    [
        (tuple[...], Err('Variable tuples must only have one type before the ellipsis', TypeError)),
        (tuple[int, str, ...], Err('Variable tuples must only have one type before the ellipsis', TypeError)),
        (
            tuple[int, Unpack[tuple[str, ...]], Unpack[tuple[str, ...]]],
            Err('More than one variadic Unpack in a type is not allowed', TypeError),
        ),
        (
            tuple[int, ..., Unpack[tuple[str, ...]]],
            Err('Cannot have a variadic Unpack and an ellipsis in the same tuple type', TypeError),
        ),
        (
            tuple[int, Unpack[tuple[int, str, ...]]],
            Err('Variable tuples must only have one type before the ellipsis', TypeError),
        ),
        # ellipsis in wrong position
        (
            tuple[..., int],
            Err('Variable tuples must end with an ellipsis', TypeError),
        ),
        (
            tuple[int, Unpack[tuple[..., int]]],
            Err('Variable tuples must end with an ellipsis', TypeError),
        ),
        # invalid unpack type
        (
            tuple[int, Unpack[int]],
            Err("Unpacked type <class 'int'> is not a tuple", TypeError),
        ),
    ],
)
def test_tuple_invalid_forms(input, expected):
    with pytest.raises(expected.exception_type, match=re.escape(expected.message)):
        TypeAdapter(input)
