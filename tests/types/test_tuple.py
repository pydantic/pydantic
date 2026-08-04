from collections import deque

import dirty_equals
import pytest
from dirty_equals import IsOneOf

from pydantic import BaseModel, ConfigDict, ValidationError


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
    class Model(BaseModel):
        v: tuple

    assert Model(v=value).v == result


@pytest.mark.parametrize('value', (pytest.param(123, id='int-123'), pytest.param('123', id='str-123')))
def test_tuple_fails(value):
    class Model(BaseModel):
        v: tuple

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'tuple_type', 'loc': ('v',), 'msg': 'Input should be a valid tuple', 'input': value}
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
    class Model(BaseModel):
        v: tuple[cls, ...]

    assert Model(v=value).v == result


@pytest.mark.parametrize(
    'value, cls, exc',
    [
        (
            ('a', 'b', [1, 2], 'c'),
            str,
            [
                {
                    'type': 'string_type',
                    'loc': ('v', 2),
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
                    'loc': ('v', 2),
                    'msg': 'Input should be a valid string',
                    'input': [1, 2],
                },
                {
                    'type': 'string_type',
                    'loc': ('v', 4),
                    'msg': 'Input should be a valid string',
                    'input': [3, 4],
                },
            ],
        ),
    ],
)
def test_tuple_variable_len_fails(value, cls, exc):
    class Model(BaseModel):
        v: tuple[cls, ...]

    with pytest.raises(ValidationError) as exc_info:
        Model(v=value)
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
    class Model(BaseModel):
        v: tuple[str, ...]

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            Model(v=value)
    else:
        assert Model(v=value).v == expected


def test_tuple_strict() -> None:
    class LaxModel(BaseModel):
        v: tuple[int, int]

        model_config = ConfigDict(strict=False)

    class StrictModel(BaseModel):
        v: tuple[int, int]

        model_config = ConfigDict(strict=True)

    assert LaxModel(v=[1, 2]).v == (1, 2)
    assert LaxModel(v=['1', 2]).v == (1, 2)
    # List should be rejected
    with pytest.raises(ValidationError) as exc_info:
        StrictModel(v=[1, 2])
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'tuple_type', 'loc': ('v',), 'msg': 'Input should be a valid tuple', 'input': [1, 2]}
    ]
    # Strict in each list item
    with pytest.raises(ValidationError) as exc_info:
        StrictModel(v=('1', 2))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('v', 0), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]
