from collections import deque

import dirty_equals
import pytest
from dirty_equals import IsOneOf

from pydantic import TypeAdapter, ValidationError


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
