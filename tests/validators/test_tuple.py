import platform
import re
from typing import Any, Dict, Type

import pytest
from dirty_equals import IsNonNegative

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err, PyAndJson


@pytest.mark.parametrize(
    'mode,items,input_value,expected',
    [
        ('variable', {'type': 'int'}, [1, 2, 3], (1, 2, 3)),
        (
            'variable',
            {'type': 'int'},
            1,
            Err('Input should be a valid tuple [kind=tuple_type, input_value=1, input_type=int]'),
        ),
        ('positional', [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}], [1, 2, '3'], (1, 2, 3)),
        (
            'positional',
            [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}],
            5,
            Err('Input should be a valid tuple [kind=tuple_type, input_value=5, input_type=int]'),
        ),
    ],
    ids=repr,
)
def test_tuple_json(py_and_json: PyAndJson, mode, items, input_value, expected):
    v = py_and_json({'type': 'tuple', 'mode': mode, 'items_schema': items})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


def test_any_no_copy():
    v = SchemaValidator('tuple')
    input_value = (1, '2', b'3')
    output = v.validate_python(input_value)
    assert output == input_value
    assert output is input_value
    assert id(output) == id(input_value)


@pytest.mark.parametrize(
    'mode,items,input_value,expected',
    [
        ('variable', {'type': 'int'}, (1, 2, '33'), (1, 2, 33)),
        ('variable', {'type': 'str'}, (b'1', b'2', '33'), ('1', '2', '33')),
        ('positional', [{'type': 'int'}, {'type': 'str'}, {'type': 'float'}], (1, b'a', 33), (1, 'a', 33.0)),
    ],
)
def test_tuple_strict_passes_with_tuple(mode, items, input_value, expected):
    v = SchemaValidator({'type': 'tuple', 'mode': mode, 'items_schema': items, 'strict': True})
    assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'mode,items', [('variable', {'type': 'int'}), ('positional', [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}])]
)
@pytest.mark.parametrize('wrong_coll_type', [list, set, frozenset])
def test_tuple_strict_fails_without_tuple(wrong_coll_type: Type[Any], mode, items):
    v = SchemaValidator({'type': 'tuple', 'mode': mode, 'items_schema': items, 'strict': True})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(wrong_coll_type([1, 2, '33']))
    assert exc_info.value.errors() == [
        {
            'kind': 'tuple_type',
            'loc': [],
            'message': 'Input should be a valid tuple',
            'input_value': wrong_coll_type([1, 2, '33']),
        }
    ]


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({}, (1, 2, 3, 4), (1, 2, 3, 4)),
        ({'min_items': 3}, (1, 2, 3, 4), (1, 2, 3, 4)),
        ({'min_items': 3}, (1, 2), Err('Input should have at least 3 items, got 2 items [kind=too_short,')),
        ({'max_items': 4}, (1, 2, 3, 4), (1, 2, 3, 4)),
        ({'max_items': 3}, (1, 2, 3, 4), Err('Input should have at most 3 items, got 4 items [kind=too_long,')),
    ],
)
def test_tuple_var_len_kwargs(kwargs: Dict[str, Any], input_value, expected):
    v = SchemaValidator({'type': 'tuple', 'mode': 'variable', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'mode,items', [('variable', {'type': 'int'}), ('positional', [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}])]
)
@pytest.mark.parametrize(
    'input_value,expected',
    [
        ((1, 2, '3'), (1, 2, 3)),
        ([1, 2, '3'], (1, 2, 3)),
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.keys(),
            (1, 2, 3),
            marks=pytest.mark.skipif(
                platform.python_implementation() == 'PyPy', reason='dict views not implemented in pyo3 for pypy'
            ),
        ),
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.values(),
            (10, 20, 30),
            marks=pytest.mark.skipif(
                platform.python_implementation() == 'PyPy', reason='dict views not implemented in pyo3 for pypy'
            ),
        ),
        ({1: 10, 2: 20, '3': '30'}, Err('Input should be a valid tuple [kind=tuple_type,')),
        # https://github.com/samuelcolvin/pydantic-core/issues/211
        ({1: 10, 2: 20, '3': '30'}.items(), Err('Input should be a valid tuple [kind=tuple_type,')),
        ({1, 2, '3'}, Err('Input should be a valid tuple [kind=tuple_type,')),
        (frozenset([1, 2, '3']), Err('Input should be a valid tuple [kind=tuple_type,')),
    ],
)
def test_tuple_validate(input_value, expected, mode, items):
    v = SchemaValidator({'type': 'tuple', 'mode': mode, 'items_schema': items})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


# Since `test_tuple_validate` is parametrized above, the generator is consumed
# on the first test run. This is a workaround to make sure the generator is
# always recreated.
@pytest.mark.parametrize(
    'mode,items', [('variable', {'type': 'int'}), ('positional', [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}])]
)
def test_tuple_validate_iterator(mode, items):
    v = SchemaValidator({'type': 'tuple', 'mode': mode, 'items_schema': items})
    assert v.validate_python((x for x in [1, 2, '3'])) == (1, 2, 3)


@pytest.mark.parametrize(
    'input_value,index',
    [
        (['wrong'], 0),
        (('wrong',), 0),
        ((1, 2, 3, 'wrong'), 3),
        ((1, 2, 3, 'wrong', 4), 3),
        ((1, 2, 'wrong'), IsNonNegative()),
    ],
)
def test_tuple_var_len_errors(input_value, index):
    v = SchemaValidator({'type': 'tuple', 'mode': 'variable', 'items_schema': {'type': 'int'}})
    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python(input_value)
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': [index],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'wrong',
        }
    ]


@pytest.mark.parametrize(
    'input_value,items,index',
    [
        (['wrong'], [{'type': 'int'}], 0),
        (('wrong',), [{'type': 'int'}], 0),
        ((1, 2, 3, 'wrong'), [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}, {'type': 'int'}], 3),
        (
            (1, 2, 3, 'wrong', 4),
            [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}, {'type': 'int'}, {'type': 'int'}],
            3,
        ),
        ((1, 2, 'wrong'), [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}], IsNonNegative()),
    ],
)
def test_tuple_fix_len_errors(input_value, items, index):
    v = SchemaValidator({'type': 'tuple', 'mode': 'positional', 'items_schema': items})
    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python(input_value)
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': [index],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'wrong',
        }
    ]


def test_multiple_missing(py_and_json: PyAndJson):
    v = py_and_json({'type': 'tuple', 'mode': 'positional', 'items_schema': ['int', 'int', 'int', 'int']})
    assert v.validate_test([1, 2, 3, 4]) == (1, 2, 3, 4)
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test([1])
    assert exc_info.value.errors() == [
        {'kind': 'missing', 'loc': [1], 'message': 'Field required', 'input_value': [1]},
        {'kind': 'missing', 'loc': [2], 'message': 'Field required', 'input_value': [1]},
        {'kind': 'missing', 'loc': [3], 'message': 'Field required', 'input_value': [1]},
    ]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test([1, 2, 3])
    assert exc_info.value.errors() == [
        {'kind': 'missing', 'loc': [3], 'message': 'Field required', 'input_value': [1, 2, 3]}
    ]


def test_extra_arguments(py_and_json: PyAndJson):
    v = py_and_json({'type': 'tuple', 'mode': 'positional', 'items_schema': ['int', 'int']})
    assert v.validate_test([1, 2]) == (1, 2)
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test([1, 2, 3, 4])
    assert exc_info.value.errors() == [
        {
            'kind': 'too_long',
            'loc': [],
            'message': 'Input should have at most 2 items, got 4 items',
            'input_value': [1, 2, 3, 4],
            'context': {'max_length': 2, 'input_length': 4},
        }
    ]


def test_positional_empty(py_and_json: PyAndJson):
    v = py_and_json({'type': 'tuple', 'mode': 'positional', 'items_schema': []})
    assert v.validate_test([]) == ()
    assert v.validate_python(()) == ()
    with pytest.raises(ValidationError, match='kind=too_long,'):
        v.validate_test([1])


def test_positional_empty_extra(py_and_json: PyAndJson):
    v = py_and_json({'type': 'tuple', 'mode': 'positional', 'items_schema': [], 'extra_schema': 'int'})
    assert v.validate_test([]) == ()
    assert v.validate_python(()) == ()
    assert v.validate_test([1]) == (1,)
    assert v.validate_test(list(range(100))) == tuple(range(100))


@pytest.mark.parametrize('input_value,expected', [((1, 2, 3), (1, 2, 3)), ([1, 2, 3], [1, 2, 3])])
def test_union_tuple_list(input_value, expected):
    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'tuple', 'mode': 'variable'}, {'type': 'list'}]})
    assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ((1, 2, 3), (1, 2, 3)),
        (('a', 'b', 'c'), ('a', 'b', 'c')),
        (('a', b'a', 'c'), ('a', 'a', 'c')),
        (
            [5],
            Err(
                '2 validation errors for union',
                errors=[
                    {
                        # first of all, not a tuple of ints ..
                        'kind': 'tuple_type',
                        'loc': ['tuple[int, ...]'],
                        'message': 'Input should be a valid tuple',
                        'input_value': [5],
                    },
                    # .. and not a tuple of strings, either
                    {
                        'kind': 'tuple_type',
                        'loc': ['tuple[str, ...]'],
                        'message': 'Input should be a valid tuple',
                        'input_value': [5],
                    },
                ],
            ),
        ),
    ],
    ids=repr,
)
def test_union_tuple_var_len(input_value, expected):
    v = SchemaValidator(
        {
            'type': 'union',
            'choices': [
                {'type': 'tuple', 'mode': 'variable', 'items_schema': {'type': 'int'}, 'strict': True},
                {'type': 'tuple', 'mode': 'variable', 'items_schema': {'type': 'str'}, 'strict': True},
            ],
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_python(input_value)
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ((1, 2, 3), (1, 2, 3)),
        (('a', 'b', 'c'), ('a', 'b', 'c')),
        (
            [5, '1', 1],
            Err(
                '2 validation errors for union',
                errors=[
                    {
                        'kind': 'tuple_type',
                        'loc': ['tuple[int, int, int]'],
                        'message': 'Input should be a valid tuple',
                        'input_value': [5, '1', 1],
                    },
                    {
                        'kind': 'tuple_type',
                        'loc': ['tuple[str, str, str]'],
                        'message': 'Input should be a valid tuple',
                        'input_value': [5, '1', 1],
                    },
                ],
            ),
        ),
    ],
    ids=repr,
)
def test_union_tuple_fix_len(input_value, expected):
    v = SchemaValidator(
        {
            'type': 'union',
            'choices': [
                {
                    'type': 'tuple',
                    'mode': 'positional',
                    'items_schema': [{'type': 'int'}, {'type': 'int'}, {'type': 'int'}],
                    'strict': True,
                },
                {
                    'type': 'tuple',
                    'mode': 'positional',
                    'items_schema': [{'type': 'str'}, {'type': 'str'}, {'type': 'str'}],
                    'strict': True,
                },
            ],
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_python(input_value)
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_python(input_value) == expected


def test_tuple_fix_error():
    v = SchemaValidator({'type': 'tuple', 'mode': 'positional', 'items_schema': ['int', 'str']})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([1])

    assert exc_info.value.errors() == [{'kind': 'missing', 'loc': [1], 'message': 'Field required', 'input_value': [1]}]


def test_tuple_fix_extra():
    v = SchemaValidator({'type': 'tuple', 'mode': 'positional', 'items_schema': ['int', 'str'], 'extra_schema': 'str'})
    assert v.validate_python([1, 'a']) == (1, 'a')
    assert v.validate_python((1, 'a')) == (1, 'a')
    assert v.validate_python((1, 'a', 'b')) == (1, 'a', 'b')
    assert v.validate_python([1, 'a', 'b', 'c', 'd']) == (1, 'a', 'b', 'c', 'd')
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([1])
    assert exc_info.value.errors() == [{'kind': 'missing', 'loc': [1], 'message': 'Field required', 'input_value': [1]}]


def test_tuple_fix_extra_any():
    v = SchemaValidator({'type': 'tuple', 'mode': 'positional', 'items_schema': ['str'], 'extra_schema': 'any'})
    assert v.validate_python([b'1']) == ('1',)
    assert v.validate_python([b'1', 2]) == ('1', 2)
    assert v.validate_python((b'1', 2)) == ('1', 2)
    assert v.validate_python([b'1', 2, b'3']) == ('1', 2, b'3')
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([])
    assert exc_info.value.errors() == [{'kind': 'missing', 'loc': [0], 'message': 'Field required', 'input_value': []}]


def test_generator_error():
    def gen(error: bool):
        yield 1
        yield 2
        if error:
            raise RuntimeError('error')
        yield 3

    v = SchemaValidator({'type': 'tuple', 'items_schema': 'int'})
    assert v.validate_python(gen(False)) == (1, 2, 3)

    with pytest.raises(ValidationError, match=r'Error iterating over object \[kind=iteration_error,'):
        v.validate_python(gen(True))
