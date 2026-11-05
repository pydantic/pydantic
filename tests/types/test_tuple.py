import re
import sys
from collections import deque
from dataclasses import dataclass

import dirty_equals
import pytest
from dirty_equals import IsOneOf
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


def test_tuple_finite_unpack():
    adapter = TypeAdapter(tuple[Unpack[tuple[int, str]], bool])

    assert adapter.validate_python(['1', '2', 1]) == (1, '2', True)


def test_tuple_unpack_serialization():
    adapter = TypeAdapter(tuple[int, Unpack[tuple[str, ...]], bool])
    value = (1, 'a', 'b', True)

    assert adapter.dump_python(value) == value
    assert adapter.dump_python(value, mode='json') == [1, 'a', 'b', True]
    assert adapter.dump_json(value) == b'[1,"a","b",true]'


@pytest.mark.skipif(sys.version_info < (3, 11), reason='Starred tuple syntax requires Python 3.11')
def test_tuple_starred_unpack(create_module):
    create_module(
        """\
from pydantic import TypeAdapter

adapter = TypeAdapter(tuple[int, *tuple[str, ...], bool])
assert adapter.validate_python(['1', '2', 1]) == (1, '2', True)
"""
    )


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
            Err("Unpacked type `<class 'int'>` is not a tuple", TypeError),
        ),
    ],
)
def test_tuple_invalid_forms(input, expected):
    with pytest.raises(expected.exception_type, match=re.escape(expected.message)):
        TypeAdapter(input)


# repeats of the above with the input as a string to to test *tuple[str, ...] syntax, can
# remove the stringification and merge with the above when Python 3.10 support dropped
@pytest.mark.skipif(sys.version_info < (3, 11), reason='Starred tuple syntax requires Python 3.11')
@pytest.mark.parametrize(
    ('input', 'expected'),
    [
        (
            'tuple[int, *tuple[str, ...], *tuple[str, ...]]',
            Err('More than one variadic Unpack in a type is not allowed', TypeError),
        ),
        (
            'tuple[int, ..., *tuple[str, ...]]',
            Err('Cannot have a variadic Unpack and an ellipsis in the same tuple type', TypeError),
        ),
        (
            'tuple[int, *tuple[int, str, ...]]',
            Err('Variable tuples must only have one type before the ellipsis', TypeError),
        ),
        ('tuple[int, *tuple[..., int]]', Err('Variable tuples must end with an ellipsis', TypeError)),
        ('tuple[*list[int]]', Err('Expected tuple type for `*` unpacking, got `*list[int]`', TypeError)),
    ],
)
def test_tuple_starred_invalid_forms(create_module, input, expected):
    with pytest.raises(expected.exception_type, match=re.escape(expected.message)):
        create_module(
            # language=Python
            f"""\
from pydantic import TypeAdapter
TypeAdapter({input})
"""
        )


@pytest.mark.parametrize(
    'value,result',
    (
        ([1, 2, '3'], (1, 2, '3')),
        ((1, 2, '3'), (1, 2, '3')),
        pytest.param((i**2 for i in range(5)), (0, 1, 4, 9, 16), marks=pytest.mark.thread_unsafe),
        (deque([1, 2, 3]), (1, 2, 3)),
        ({1, '2'}, IsOneOf((1, '2'), ('2', 1))),
    ),
)
def test_tuple_success(value, result):
    ta = TypeAdapter(tuple)

    assert ta.validate_python(value) == result


@pytest.mark.parametrize('value', (pytest.param(123, id='int-123'), pytest.param('123', id='str-123')))
def test_tuple_fails(value):
    ta = TypeAdapter(tuple)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'tuple_type', 'loc': (), 'msg': 'Input should be a valid tuple', 'input': value}
    ]


@pytest.mark.parametrize(
    'value,cls,result',
    (
        ([1, 2, '3'], int, (1, 2, 3)),
        ((1, 2, '3'), int, (1, 2, 3)),
        pytest.param((i**2 for i in range(5)), int, (0, 1, 4, 9, 16), marks=pytest.mark.thread_unsafe),
        (('a', 'b', 'c'), str, ('a', 'b', 'c')),
    ),
)
def test_tuple_variable_len_success(value, cls, result):
    ta = TypeAdapter(tuple[cls, ...])

    assert ta.validate_python(value) == result


@pytest.mark.parametrize(
    'value, cls, exc',
    [
        (
            ('a', 'b', [1, 2], 'c'),
            str,
            [
                {
                    'type': 'string_type',
                    'loc': (2,),
                    'msg': 'Input should be a valid string',
                    'input': [1, 2],
                }
            ],
        ),
        (
            ('a', 'b', [1, 2], 'c', [3, 4]),
            str,
            [
                {
                    'type': 'string_type',
                    'loc': (2,),
                    'msg': 'Input should be a valid string',
                    'input': [1, 2],
                },
                {
                    'type': 'string_type',
                    'loc': (4,),
                    'msg': 'Input should be a valid string',
                    'input': [3, 4],
                },
            ],
        ),
    ],
)
def test_tuple_variable_len_fails(value, cls, exc):
    ta = TypeAdapter(tuple[cls, ...])

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(value)
    assert exc_info.value.errors(include_url=False) == exc


@pytest.mark.parametrize(
    'value,expected',
    [
        (('1', '2'), ('1', '2')),
        (['1', '2'], ('1', '2')),
        ({'1': 1, '2': 2}.keys(), ('1', '2')),
        ({'1': '1', '2': '2'}.values(), ('1', '2')),
        ({'1', '2'}, dirty_equals.IsOneOf(('1', '2'), ('2', '1'))),
        (frozenset(['1', '2']), dirty_equals.IsOneOf(('1', '2'), ('2', '1'))),
        ({'1': 1, '2': 2}, ValidationError),
    ],
)
def test_tuple_validation(value, expected):
    ta = TypeAdapter(tuple[str, ...])

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            ta.validate_python(value)
    else:
        assert ta.validate_python(value) == expected


def test_tuple_strict() -> None:
    ta = TypeAdapter(tuple[int, int])

    assert ta.validate_python([1, 2]) == (1, 2)
    assert ta.validate_python(['1', 2]) == (1, 2)
    # List should be rejected
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python([1, 2], strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'tuple_type', 'loc': (), 'msg': 'Input should be a valid tuple', 'input': [1, 2]}
    ]
    # Strict in each list item
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(('1', 2), strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': (0,), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]
