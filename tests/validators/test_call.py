import dataclasses
import re
from collections import namedtuple

import pytest

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err, PyAndJson, plain_repr


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [(1, 2, 3), 6],
        [{'a': 1, 'b': 1, 'c': 1}, 3],
        [{'__args__': (1,), '__kwargs__': {'b': 1, 'c': 1}}, 3],
        [(1, 2, 'x'), Err('arguments -> 2\n  Input should be a valid integer,')],
        [(3, 3, 4), 10],
        [(3, 3, 5), Err('return-value\n  Input should be less than or equal to 10')],
    ],
)
def test_function_call_arguments(py_and_json: PyAndJson, input_value, expected):
    def my_function(a, b, c):
        return a + b + c

    v = py_and_json(
        {
            'type': 'call',
            'function': my_function,
            'arguments_schema': {
                'type': 'arguments',
                'arguments_schema': [
                    {'name': 'a', 'mode': 'positional_or_keyword', 'schema': {'type': 'int'}},
                    {'name': 'b', 'mode': 'positional_or_keyword', 'schema': {'type': 'int'}},
                    {'name': 'c', 'mode': 'positional_or_keyword', 'schema': {'type': 'int'}},
                ],
            },
            'return_schema': {'type': 'int', 'le': 10},
        }
    )

    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_python(input_value)
        # debug(exc_info.value.errors())
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [((1, 2, 3), {}), 6],
        [((1, 2, 3), {}), 6],
        [{'a': 1, 'b': 1, 'c': 1}, 3],
        ['x', TypeError('Arguments validator should return a tuple')],
        # lists are not allowed, input must strictly be a tuple
        [[(1, 2, 3), {}], TypeError('Arguments validator should return a tuple')],
        [((1, 2, 3, 4), {}), TypeError('my_function() takes 3 positional arguments but 4 were given')],
        [{'a': 1, 'b': 1, 'c': 1, 'd': 1}, TypeError("my_function() got an unexpected keyword argument 'd'")],
    ],
)
def test_function_args_any(input_value, expected):
    def my_function(a, b, c):
        return a + b + c

    v = SchemaValidator(
        {'type': 'call', 'function': my_function, 'arguments_schema': {'type': 'any'}, 'return_schema': {'type': 'int'}}
    )

    if isinstance(expected, Exception):
        with pytest.raises(type(expected), match=re.escape(str(expected))):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize('input_value,expected', [[((1,), {}), 1], [(('abc',), {}), 'abc']])
def test_function_return_any(input_value, expected):
    def my_function(a):
        return a

    v = SchemaValidator({'type': 'call', 'function': my_function, 'arguments_schema': {'type': 'any'}})
    assert 'name:"call[my_function]"' in plain_repr(v)

    assert v.validate_python(input_value) == expected


def test_in_union():
    def my_function(a):
        return a

    v = SchemaValidator(
        {
            'type': 'union',
            'choices': [
                {
                    'type': 'call',
                    'function': my_function,
                    'arguments_schema': {
                        'type': 'arguments',
                        'arguments_schema': [{'name': 'a', 'mode': 'positional_or_keyword', 'schema': {'type': 'int'}}],
                    },
                },
                {'type': 'int'},
            ],
        }
    )
    assert v.validate_python((1,)) == 1
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python((1, 2))
    assert exc_info.value.errors() == [
        {
            'type': 'unexpected_positional_argument',
            'loc': ('call[my_function]', 'arguments', 1),
            'msg': 'Unexpected positional argument',
            'input': 2,
        },
        {'type': 'int_type', 'loc': ('int',), 'msg': 'Input should be a valid integer', 'input': (1, 2)},
    ]


def test_dataclass():
    @dataclasses.dataclass
    class my_dataclass:
        a: int
        b: str

    v = SchemaValidator(
        {
            'type': 'call',
            'function': my_dataclass,
            'arguments_schema': {
                'type': 'arguments',
                'arguments_schema': [
                    {'name': 'a', 'mode': 'positional_or_keyword', 'schema': {'type': 'int'}},
                    {'name': 'b', 'mode': 'positional_or_keyword', 'schema': {'type': 'str'}},
                ],
            },
        }
    )
    d = v.validate_python(('1', b'2'))
    assert dataclasses.is_dataclass(d)
    assert d.a == 1
    assert d.b == '2'
    d = v.validate_python({'a': 1, 'b': '2'})
    assert dataclasses.is_dataclass(d)
    assert d.a == 1
    assert d.b == '2'
    assert 'name:"call[my_dataclass]"' in plain_repr(v)


def test_named_tuple():
    Point = namedtuple('Point', ['x', 'y'])

    v = SchemaValidator(
        {
            'type': 'call',
            'function': Point,
            'arguments_schema': {
                'type': 'arguments',
                'arguments_schema': [
                    {'name': 'x', 'mode': 'positional_or_keyword', 'schema': {'type': 'float'}},
                    {'name': 'y', 'mode': 'positional_or_keyword', 'schema': {'type': 'float'}},
                ],
            },
        }
    )
    d = v.validate_python(('1.1', '2.2'))
    assert isinstance(d, Point)
    assert d.x == 1.1
    assert d.y == 2.2

    d = v.validate_python({'x': 1.1, 'y': 2.2})
    assert isinstance(d, Point)
    assert d.x == 1.1
    assert d.y == 2.2
