import re
from collections import OrderedDict
from collections.abc import Mapping

import pytest
from dirty_equals import HasRepr, IsStr

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err


def test_dict(py_or_json):
    v = py_or_json({'type': 'dict', 'keys_schema': {'type': 'int'}, 'values_schema': {'type': 'int'}})
    assert v.validate_test({'1': 2, '3': 4}) == {1: 2, 3: 4}
    v = py_or_json({'type': 'dict', 'strict': True, 'keys_schema': {'type': 'int'}, 'values_schema': {'type': 'int'}})
    assert v.validate_test({'1': 2, '3': 4}) == {1: 2, 3: 4}
    assert v.validate_test({}) == {}
    with pytest.raises(ValidationError, match='Value must be a valid dictionary'):
        v.validate_test([])


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({'1': 1, '2': 2}, {'1': '1', '2': '2'}),
        (OrderedDict(a=1, b=2), {'a': '1', 'b': '2'}),
        ({}, {}),
        ('foobar', Err("Value must be a valid dictionary [kind=dict_type, input_value='foobar', input_type=str]")),
        ([], Err('Value must be a valid dictionary [kind=dict_type,')),
        ([('x', 'y')], Err('Value must be a valid dictionary [kind=dict_type,')),
        ([('x', 'y'), ('z', 'z')], Err('Value must be a valid dictionary [kind=dict_type,')),
        ((), Err('Value must be a valid dictionary [kind=dict_type,')),
        ((('x', 'y'),), Err('Value must be a valid dictionary [kind=dict_type,')),
        ((type('Foobar', (), {'x': 1})()), Err('Value must be a valid dictionary [kind=dict_type,')),
    ],
    ids=repr,
)
def test_dict_cases(input_value, expected):
    v = SchemaValidator({'type': 'dict', 'keys_schema': 'str', 'values_schema': 'str'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


def test_dict_value_error(py_or_json):
    v = py_or_json({'type': 'dict', 'values_schema': 'int'})
    assert v.validate_test({'a': 2, 'b': '4'}) == {'a': 2, 'b': 4}
    with pytest.raises(ValidationError, match='Value must be a valid integer') as exc_info:
        v.validate_test({'a': 2, 'b': 'wrong'})
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': ['b'],
            'message': 'Value must be a valid integer, unable to parse string as an integer',
            'input_value': 'wrong',
        }
    ]


def test_dict_error_key_int():
    v = SchemaValidator({'type': 'dict', 'values_schema': 'int'})
    with pytest.raises(ValidationError, match='Value must be a valid integer') as exc_info:
        v.validate_python({1: 2, 3: 'wrong'})
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': [3],
            'message': 'Value must be a valid integer, unable to parse string as an integer',
            'input_value': 'wrong',
        }
    ]


def test_dict_error_key_other():
    v = SchemaValidator({'type': 'dict', 'values_schema': 'int'})
    with pytest.raises(ValidationError, match='Value must be a valid integer') as exc_info:
        v.validate_python({1: 2, (1, 2): 'wrong'})
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': ['(1, 2)'],
            'message': 'Value must be a valid integer, unable to parse string as an integer',
            'input_value': 'wrong',
        }
    ]


def test_dict_any_value():
    v = SchemaValidator({'type': 'dict', 'keys_schema': {'type': 'str'}})
    v = SchemaValidator({'type': 'dict', 'keys_schema': {'type': 'str'}})
    assert v.validate_python({'1': 1, '2': 'a', '3': None}) == {'1': 1, '2': 'a', '3': None}


def test_mapping():
    class MyMapping(Mapping):
        def __init__(self, d):
            self._d = d

        def __getitem__(self, key):
            return self._d[key]

        def __iter__(self):
            return iter(self._d)

        def __len__(self):
            return len(self._d)

    v = SchemaValidator({'type': 'dict', 'keys_schema': {'type': 'int'}, 'values_schema': {'type': 'int'}})
    assert v.validate_python(MyMapping({'1': 2, 3: '4'})) == {1: 2, 3: 4}
    v = SchemaValidator(
        {'type': 'dict', 'strict': True, 'keys_schema': {'type': 'int'}, 'values_schema': {'type': 'int'}}
    )
    with pytest.raises(ValidationError, match='Value must be a valid dictionary'):
        v.validate_python(MyMapping({'1': 2, 3: '4'}))


def test_key_error():
    v = SchemaValidator({'type': 'dict', 'keys_schema': {'type': 'int'}, 'values_schema': {'type': 'int'}})
    assert v.validate_python({'1': True}) == {1: 1}
    with pytest.raises(ValidationError, match=re.escape('x -> [key]\n  Value must be a valid integer')) as exc_info:
        v.validate_python({'x': 1})
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': ['x', '[key]'],
            'message': 'Value must be a valid integer, unable to parse string as an integer',
            'input_value': 'x',
        }
    ]


def test_mapping_error():
    class BadMapping(Mapping):
        def __getitem__(self, key):
            raise None

        def __iter__(self):
            raise RuntimeError('intentional error')

        def __len__(self):
            return 1

    v = SchemaValidator({'type': 'dict', 'keys_schema': {'type': 'int'}, 'values_schema': {'type': 'int'}})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(BadMapping())

    assert exc_info.value.errors() == [
        {
            'kind': 'dict_from_mapping',
            'loc': [],
            'message': 'Unable to convert mapping to a dictionary, error: RuntimeError: intentional error',
            'input_value': HasRepr(IsStr(regex='.+BadMapping object at.+')),
            'context': {'error': 'RuntimeError: intentional error'},
        }
    ]


def test_mapping_error_yield_1():
    class BadMapping(Mapping):
        def items(self):
            return [(1,)]

        def __iter__(self):
            return iter({1: 2})

        def __getitem__(self, key):
            raise None

        def __len__(self):
            return 1

    v = SchemaValidator({'type': 'dict', 'keys_schema': {'type': 'int'}, 'values_schema': {'type': 'int'}})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(BadMapping())

    assert exc_info.value.errors() == [
        {
            'kind': 'dict_from_mapping',
            'loc': [],
            'message': (
                'Unable to convert mapping to a dictionary, error: '
                'TypeError: mapping items must be a tuple with 2 elements'
            ),
            'input_value': HasRepr(IsStr(regex='.+BadMapping object at.+')),
            'context': {'error': 'TypeError: mapping items must be a tuple with 2 elements'},
        }
    ]


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({}, {'1': 1, '2': 2}, {'1': 1, '2': 2}),
        (
            {'min_items': 3},
            {'1': 1, '2': 2, '3': 3.0, '4': [1, 2, 3, 4]},
            {'1': 1, '2': 2, '3': 3.0, '4': [1, 2, 3, 4]},
        ),
        ({'min_items': 3}, {1: '2', 3: '4'}, Err('Dict must have at least 3 items [kind=too_short')),
        ({'max_items': 4}, {'1': 1, '2': 2, '3': 3.0}, {'1': 1, '2': 2, '3': 3.0}),
        (
            {'max_items': 3},
            {'1': 1, '2': 2, '3': 3.0, '4': [1, 2, 3, 4]},
            Err('Dict must have at most 3 items [kind=too_long'),
        ),
    ],
)
def test_dict_length_constraints(kwargs, input_value, expected):
    v = SchemaValidator({'type': 'dict', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected
