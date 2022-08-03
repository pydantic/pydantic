import platform
import re
from typing import Any, Dict

import pytest

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err, PyAndJson


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([], set()),
        ([1, 2, 3], {1, 2, 3}),
        ([1, 2, '3'], {1, 2, 3}),
        ([1, 2, 3, 2, 3], {1, 2, 3}),
        (5, Err('Input should be a valid set [kind=set_type, input_value=5, input_type=int]')),
    ],
)
def test_set_ints_both(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'set', 'items_schema': {'type': 'int'}})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize('input_value,expected', [([1, 2.5, '3'], {1, 2.5, '3'})])
def test_set_no_validators_both(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'set'})
    assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ([1, 2.5, '3'], {1, 2.5, '3'}),
        ('foo', Err('Input should be a valid set')),
        (1, Err('Input should be a valid set')),
        (1.0, Err('Input should be a valid set')),
        (False, Err('Input should be a valid set')),
    ],
)
def test_frozenset_no_validators_both(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'set'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({1, 2, 3}, {1, 2, 3}),
        (set(), set()),
        ([1, 2, 3, 2, 3], {1, 2, 3}),
        ([], set()),
        ((1, 2, 3, 2, 3), {1, 2, 3}),
        ((), set()),
        (frozenset([1, 2, 3, 2, 3]), {1, 2, 3}),
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.keys(),
            {1, 2, 3},
            marks=pytest.mark.skipif(
                platform.python_implementation() == 'PyPy', reason='dict views not implemented in pyo3 for pypy'
            ),
        ),
        pytest.param(
            {1: 10, 2: 20, '3': '30'}.values(),
            {10, 20, 30},
            marks=pytest.mark.skipif(
                platform.python_implementation() == 'PyPy', reason='dict views not implemented in pyo3 for pypy'
            ),
        ),
        ({1: 10, 2: 20, '3': '30'}, Err('Input should be a valid set [kind=set_type,')),
        # https://github.com/samuelcolvin/pydantic-core/issues/211
        ({1: 10, 2: 20, '3': '30'}.items(), Err('Input should be a valid set [kind=set_type,')),
        ((x for x in [1, 2, '3']), {1, 2, 3}),
        ({'abc'}, Err('0\n  Input should be a valid integer')),
        ({1: 2}, Err('1 validation error for set[int]\n  Input should be a valid set')),
        ('abc', Err('Input should be a valid set')),
    ],
)
def test_set_ints_python(input_value, expected):
    v = SchemaValidator({'type': 'set', 'items_schema': {'type': 'int'}})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize('input_value,expected', [([1, 2.5, '3'], {1, 2.5, '3'}), ([(1, 2), (3, 4)], {(1, 2), (3, 4)})])
def test_set_no_validators_python(input_value, expected):
    v = SchemaValidator({'type': 'set'})
    assert v.validate_python(input_value) == expected


def test_set_multiple_errors():
    v = SchemaValidator({'type': 'set', 'items_schema': {'type': 'int'}})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(['a', (1, 2), []])
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': [0],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'a',
        },
        {'kind': 'int_type', 'loc': [1], 'message': 'Input should be a valid integer', 'input_value': (1, 2)},
        {'kind': 'int_type', 'loc': [2], 'message': 'Input should be a valid integer', 'input_value': []},
    ]


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({'strict': True}, {1, 2, 3}, {1, 2, 3}),
        ({'strict': True}, set(), set()),
        ({'strict': True}, [1, 2, 3, 2, 3], Err('Input should be a valid set [kind=set_type,')),
        ({'strict': True}, [], Err('Input should be a valid set [kind=set_type,')),
        ({'strict': True}, (), Err('Input should be a valid set [kind=set_type,')),
        ({'strict': True}, (1, 2, 3), Err('Input should be a valid set [kind=set_type,')),
        ({'strict': True}, frozenset([1, 2, 3]), Err('Input should be a valid set [kind=set_type,')),
        ({'strict': True}, 'abc', Err('Input should be a valid set [kind=set_type,')),
        ({'min_items': 3}, {1, 2, 3}, {1, 2, 3}),
        ({'min_items': 3}, {1, 2}, Err('Input should have at least 3 items, got 2 items [kind=too_short,')),
        ({'max_items': 3}, {1, 2, 3}, {1, 2, 3}),
        ({'max_items': 3}, {1, 2, 3, 4}, Err('Input should have at most 3 items, got 4 items [kind=too_long,')),
    ],
)
def test_set_kwargs(kwargs: Dict[str, Any], input_value, expected):
    v = SchemaValidator({'type': 'set', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize('input_value,expected', [({1, 2, 3}, {1, 2, 3}), ([1, 2, 3], [1, 2, 3])])
def test_union_set_list(input_value, expected):
    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'set'}, {'type': 'list'}]})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({1, 2, 3}, {1, 2, 3}),
        ({'a', 'b', 'c'}, {'a', 'b', 'c'}),
        (
            [1, 'a'],
            Err(
                '2 validation errors for union',
                errors=[
                    {
                        'kind': 'int_type',
                        'loc': ['set[int]', 1],
                        'message': 'Input should be a valid integer',
                        'input_value': 'a',
                    },
                    # second because validation on the string choice comes second
                    {
                        'kind': 'str_type',
                        'loc': ['set[str]', 0],
                        'message': 'Input should be a valid string',
                        'input_value': 1,
                    },
                ],
            ),
        ),
    ],
)
def test_union_set_int_set_str(input_value, expected):
    v = SchemaValidator(
        {
            'type': 'union',
            'choices': [
                {'type': 'set', 'items_schema': {'type': 'int', 'strict': True}},
                {'type': 'set', 'items_schema': {'type': 'str', 'strict': True}},
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


def test_set_as_dict_keys(py_and_json: PyAndJson):
    v = py_and_json({'type': 'dict', 'keys_schema': {'type': 'set'}, 'values_schema': 'int'})
    with pytest.raises(ValidationError, match=re.escape('Input should be a valid set')):
        v.validate_test({'foo': 'bar'})


def test_generator_error():
    def gen(error: bool):
        yield 1
        yield 2
        if error:
            raise RuntimeError('error')
        yield 3

    v = SchemaValidator({'type': 'set', 'items_schema': 'int'})
    r = v.validate_python(gen(False))
    assert r == {1, 2, 3}
    assert isinstance(r, set)

    with pytest.raises(ValidationError, match=r'Error iterating over object \[kind=iteration_error,'):
        v.validate_python(gen(True))
