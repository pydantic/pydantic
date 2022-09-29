import platform
import re
from typing import Any, Dict

import pytest
from dirty_equals import HasRepr, IsStr

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err, PyAndJson


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, 2, 3], [1, 2, 3]),
        ([1, 2, '3'], [1, 2, 3]),
        (5, Err('Input should be a valid list/array [kind=list_type, input_value=5, input_type=int]')),
        ('5', Err("Input should be a valid list/array [kind=list_type, input_value='5', input_type=str]")),
    ],
)
def test_list_json(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'list', 'items_schema': {'type': 'int'}})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


def test_list_strict():
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}, 'strict': True})
    assert v.validate_python([1, 2, '33']) == [1, 2, 33]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python((1, 2, '33'))
    assert exc_info.value.errors() == [
        {'kind': 'list_type', 'loc': [], 'message': 'Input should be a valid list/array', 'input_value': (1, 2, '33')}
    ]


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, 2, '3'], [1, 2, 3]),
        ((1, 2, '3'), [1, 2, 3]),
        ({1, 2, '3'}, Err('Input should be a valid list/array [kind=list_type,')),
        (frozenset({1, 2, '3'}), Err('Input should be a valid list/array [kind=list_type,')),
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.keys(),
            [1, 2, 3],
            marks=pytest.mark.skipif(
                platform.python_implementation() == 'PyPy', reason='dict views not implemented in pyo3 for pypy'
            ),
        ),
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.values(),
            [10, 20, 30],
            marks=pytest.mark.skipif(
                platform.python_implementation() == 'PyPy', reason='dict views not implemented in pyo3 for pypy'
            ),
        ),
        ({1: 10, 2: 20, '3': '30'}, Err('Input should be a valid list/array [kind=list_type,')),
        ((x for x in [1, 2, '3']), [1, 2, 3]),
    ],
)
def test_list_int(input_value, expected):
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([], []),
        ([1, '2', b'3'], [1, '2', b'3']),
        (frozenset([1, '2', b'3']), Err('Input should be a valid list/array [kind=list_type,')),
        ((), []),
        ((1, '2', b'3'), [1, '2', b'3']),
        ({1, '2', b'3'}, Err('Input should be a valid list/array [kind=list_type,')),
    ],
)
def test_list_any(input_value, expected):
    v = SchemaValidator({'type': 'list'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,index', [(['wrong'], 0), (('wrong',), 0), ([1, 2, 3, 'wrong'], 3), ((1, 2, 3, 'wrong', 4), 3)]
)
def test_list_error(input_value, index):
    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(input_value)
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': [index],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'wrong',
        }
    ]


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({}, [1, 2, 3, 4], [1, 2, 3, 4]),
        ({'min_length': 3}, [1, 2, 3, 4], [1, 2, 3, 4]),
        ({'min_length': 3}, [1, 2], Err('Input should have at least 3 items, got 2 items [kind=too_short,')),
        ({'min_length': 1}, [], Err('Input should have at least 1 item, got 0 items [kind=too_short,')),
        ({'max_length': 4}, [1, 2, 3, 4], [1, 2, 3, 4]),
        ({'max_length': 3}, [1, 2, 3, 4], Err('Input should have at most 3 items, got 4 items [kind=too_long,')),
        ({'max_length': 1}, [1, 2], Err('Input should have at most 1 item, got 2 items [kind=too_long,')),
    ],
)
def test_list_length_constraints(kwargs: Dict[str, Any], input_value, expected):
    v = SchemaValidator({'type': 'list', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


def test_length_ctx():
    v = SchemaValidator({'type': 'list', 'min_length': 2, 'max_length': 3})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([1])
    assert exc_info.value.errors() == [
        {
            'kind': 'too_short',
            'loc': [],
            'message': 'Input should have at least 2 items, got 1 item',
            'input_value': [1],
            'context': {'min_length': 2, 'input_length': 1},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([1, 2, 3, 4])

    assert exc_info.value.errors() == [
        {
            'kind': 'too_long',
            'loc': [],
            'message': 'Input should have at most 3 items, got 4 items',
            'input_value': [1, 2, 3, 4],
            'context': {'max_length': 3, 'input_length': 4},
        }
    ]


def test_list_function():
    def f(input_value, **kwargs):
        return input_value * 2

    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'function', 'mode': 'plain', 'function': f}})

    assert v.validate_python([1, 2, 3]) == [2, 4, 6]


def test_list_function_val_error():
    def f(input_value, **kwargs):
        raise ValueError(f'error {input_value}')

    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'function', 'mode': 'plain', 'function': f}})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([1, 2])
    assert exc_info.value.errors() == [
        {
            'kind': 'value_error',
            'loc': [0],
            'message': 'Value error, error 1',
            'input_value': 1,
            'context': {'error': 'error 1'},
        },
        {
            'kind': 'value_error',
            'loc': [1],
            'message': 'Value error, error 2',
            'input_value': 2,
            'context': {'error': 'error 2'},
        },
    ]


def test_list_function_internal_error():
    def f(input_value, **kwargs):
        raise RuntimeError(f'error {input_value}')

    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'function', 'mode': 'plain', 'function': f}})

    with pytest.raises(RuntimeError, match='^error 1$') as exc_info:
        v.validate_python([1, 2])
    assert exc_info.value.args[0] == 'error 1'


def test_generator_error():
    def gen(error: bool):
        yield 1
        yield 2
        if error:
            raise RuntimeError('error')
        yield 3

    v = SchemaValidator({'type': 'list', 'items_schema': {'type': 'int'}})
    assert v.validate_python(gen(False)) == [1, 2, 3]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(gen(True))
    assert exc_info.value.errors() == [
        {
            'kind': 'iteration_error',
            'loc': [],
            'message': 'Error iterating over object',
            'input_value': HasRepr(IsStr(regex='<generator object test_generator_error.<locals>.gen at 0x[0-9a-f]+>')),
        }
    ]


@pytest.mark.skipif(platform.python_implementation() == 'PyPy', reason='dict views not implemented in pyo3 for pypy')
@pytest.mark.parametrize(
    'input_value,items_schema,expected',
    [
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.items(),
            {'type': 'tuple', 'items_schema': {'type': 'any'}},
            [(1, 10), (2, 20), ('3', '30')],
            id='Tuple[Any, Any]',
        ),
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.items(),
            {'type': 'tuple', 'items_schema': {'type': 'int'}},
            [(1, 10), (2, 20), (3, 30)],
            id='Tuple[int, int]',
        ),
        pytest.param({1: 10, 2: 20, '3': '30'}.items(), {'type': 'any'}, [(1, 10), (2, 20), ('3', '30')], id='Any'),
    ],
)
def test_list_from_dict_items(input_value, items_schema, expected):
    v = SchemaValidator({'type': 'list', 'items_schema': items_schema})
    output = v.validate_python(input_value)
    assert isinstance(output, list)
    assert output == expected
