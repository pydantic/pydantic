from collections import deque
from collections.abc import MutableSequence
from typing import Annotated

import annotated_types
import dirty_equals
import pytest
from dirty_equals import IsOneOf

from pydantic import BaseModel, Field, TypeAdapter, ValidationError


@pytest.mark.parametrize(
    'value,result',
    (
        ([1, 2, '3'], [1, 2, '3']),
        ((1, 2, '3'), [1, 2, '3']),
        pytest.param((i**2 for i in range(5)), [0, 1, 4, 9, 16], marks=pytest.mark.thread_unsafe),
        (deque([1, 2, 3]), [1, 2, 3]),
        ({1, '2'}, IsOneOf([1, '2'], ['2', 1])),
    ),
)
def test_list_success(value, result):
    ta = TypeAdapter(list)

    assert ta.validate_python(value) == result


@pytest.mark.parametrize('value', (pytest.param(123, id='int-123'), pytest.param('123', id='str-123')))
def test_list_fails(value):
    ta = TypeAdapter(list)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(value)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'list_type',
            'loc': (),
            'msg': 'Input should be a valid list',
            'input': value,
        }
    ]


def test_list_type_fails():
    ta = TypeAdapter(list[int])

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('123')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'list_type', 'loc': (), 'msg': 'Input should be a valid list', 'input': '123'}
    ]


@pytest.mark.parametrize(
    'value,expected',
    [
        (['1', '2'], ['1', '2']),
        (('1', '2'), ['1', '2']),
        ({'1': 1, '2': 2}.keys(), ['1', '2']),
        ({'1': '1', '2': '2'}.values(), ['1', '2']),
        ({'1', '2'}, dirty_equals.IsOneOf(['1', '2'], ['2', '1'])),
        (frozenset(['1', '2']), dirty_equals.IsOneOf(['1', '2'], ['2', '1'])),
        ({'1': 1, '2': 2}, ValidationError),
    ],
)
def test_list_validation(value, expected):
    ta = TypeAdapter(list[str])

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            ta.validate_python(value)
    else:
        assert ta.validate_python(value) == expected


def test_constrained_list_good():
    ta = TypeAdapter(list[int])

    assert ta.validate_python([1, 2, 3]) == [1, 2, 3]


def test_constrained_list_default():
    class ConListModelMax(BaseModel):
        v: list[int] = []

    m = ConListModelMax()
    assert m.v == []


def test_constrained_list_too_long():
    ta = TypeAdapter(Annotated[list[int], annotated_types.Len(0, 10)])

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(list(str(i) for i in range(11)))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': (),
            'msg': 'List should have at most 10 items after validation, not 11',
            'input': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
            'ctx': {'field_type': 'List', 'max_length': 10, 'actual_length': 11},
        }
    ]


def test_constrained_list_too_short():
    ta = TypeAdapter(Annotated[list[int], annotated_types.Len(1)])

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python([])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': (),
            'msg': 'List should have at least 1 item after validation, not 0',
            'input': [],
            'ctx': {'field_type': 'List', 'min_length': 1, 'actual_length': 0},
        }
    ]


def test_constrained_list_optional():
    class Model(BaseModel):
        req: Annotated[list[str], annotated_types.Len(1)] | None
        opt: Annotated[list[str], annotated_types.Len(1)] | None = None

    assert Model(req=None).model_dump() == {'req': None, 'opt': None}
    assert Model(req=None, opt=None).model_dump() == {'req': None, 'opt': None}

    with pytest.raises(ValidationError) as exc_info:
        Model(req=[], opt=[])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('req',),
            'msg': 'List should have at least 1 item after validation, not 0',
            'input': [],
            'ctx': {'field_type': 'List', 'min_length': 1, 'actual_length': 0},
        },
        {
            'type': 'too_short',
            'loc': ('opt',),
            'msg': 'List should have at least 1 item after validation, not 0',
            'input': [],
            'ctx': {'field_type': 'List', 'min_length': 1, 'actual_length': 0},
        },
    ]

    assert Model(req=['a'], opt=['a']).model_dump() == {'req': ['a'], 'opt': ['a']}


def test_constrained_list_constraints():
    ta = TypeAdapter(Annotated[list[int], annotated_types.Len(7, 11)])

    assert ta.validate_python(list(range(7))) == list(range(7))
    assert ta.validate_python(list(range(11))) == list(range(11))

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(list(range(6)))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': (),
            'msg': 'List should have at least 7 items after validation, not 6',
            'input': [0, 1, 2, 3, 4, 5],
            'ctx': {'field_type': 'List', 'min_length': 7, 'actual_length': 6},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(list(range(12)))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': (),
            'msg': 'List should have at most 11 items after validation, not 12',
            'input': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            'ctx': {'field_type': 'List', 'max_length': 11, 'actual_length': 12},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(1)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'list_type', 'loc': (), 'msg': 'Input should be a valid list', 'input': 1}
    ]


def test_constrained_list_item_type_fails():
    ta = TypeAdapter(list[int])

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(['a', 'b', 'c'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (0,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        },
        {
            'type': 'int_parsing',
            'loc': (1,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'b',
        },
        {
            'type': 'int_parsing',
            'loc': (2,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'c',
        },
    ]


def test_constrained_list():
    ta = TypeAdapter(Annotated[list[int], Field(min_length=2, max_length=4)])

    assert ta.validate_python([1, 2]) == [1, 2]

    msg = r'List should have at least 2 items after validation, not 1 \[type=too_short,'
    with pytest.raises(ValidationError, match=msg):
        ta.validate_python([1])

    msg = r'List should have at most 4 items after validation, not 5 \[type=too_long,'
    with pytest.raises(ValidationError, match=msg):
        ta.validate_python(list(range(5)))

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python([1, 'x', 'y'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (1,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'x',
        },
        {
            'type': 'int_parsing',
            'loc': (2,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'y',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(1)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'list_type', 'loc': (), 'msg': 'Input should be a valid list', 'input': 1}
    ]


def test_list_wrong_type_default():
    """It should not validate default value by default"""

    class Model(BaseModel):
        v: list[int] = 'a'

    m = Model()
    assert m.v == 'a'


def test_list_strict() -> None:
    ta = TypeAdapter(list[int])

    assert ta.validate_python((1, 2)) == [1, 2]
    assert ta.validate_python(('1', 2)) == [1, 2]
    # Tuple should be rejected
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python((1, 2), strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'list_type', 'loc': (), 'msg': 'Input should be a valid list', 'input': (1, 2)}
    ]
    # Strict in each list item
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(['1', 2], strict=True)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': (0,), 'msg': 'Input should be a valid integer', 'input': '1'}
    ]


def test_bare_mutable_sequence() -> None:
    """A bare `MutableSequence` should behave as a bare `list`, as `MutableSequence[int]` does."""
    ta = TypeAdapter(MutableSequence)

    assert ta.validate_python([1, '2']) == [1, '2']
    assert ta.validate_python((1, '2')) == [1, '2']

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('abc')
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'list_type', 'loc': (), 'msg': 'Input should be a valid list', 'input': 'abc'}
    ]
