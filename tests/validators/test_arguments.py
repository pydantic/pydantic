import re
import sys
from functools import wraps
from inspect import Parameter, signature
from typing import Any, get_type_hints

import pytest
from dirty_equals import IsListOrTuple

from pydantic_core import SchemaError, SchemaValidator, ValidationError

from ..conftest import Err, PyAndJson, plain_repr


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [((1, 'a', True), None), ((1, 'a', True), {})],
        [((1, 'a', True), {}), ((1, 'a', True), {})],
        [([1, 'a', True], None), ((1, 'a', True), {})],
        [((1, 'a', 'true'), None), ((1, 'a', True), {})],
        ['x', Err('kind=arguments_type,')],
        [((1, 'a', True), ()), Err('kind=arguments_type,')],
        [(4, {}), Err('kind=arguments_type,')],
        [(1, 2, 3), Err('kind=arguments_type,')],
        [
            ([1, 'a', True], {'x': 1}),
            Err(
                '',
                [
                    {
                        'kind': 'unexpected_keyword_argument',
                        'loc': ['x'],
                        'message': 'Unexpected keyword argument',
                        'input_value': 1,
                    }
                ],
            ),
        ],
        [
            ([1], None),
            Err(
                '',
                [
                    {
                        'kind': 'missing_positional_argument',
                        'loc': [1],
                        'message': 'Missing required positional argument',
                        'input_value': IsListOrTuple([1], None),
                    },
                    {
                        'kind': 'missing_positional_argument',
                        'loc': [2],
                        'message': 'Missing required positional argument',
                        'input_value': IsListOrTuple([1], None),
                    },
                ],
            ),
        ],
        [
            ([1, 'a', True, 4], None),
            Err(
                '',
                [
                    {
                        'kind': 'unexpected_positional_argument',
                        'loc': [3],
                        'message': 'Unexpected positional argument',
                        'input_value': 4,
                    }
                ],
            ),
        ],
        [
            ([1, 'a', True, 4, 5], None),
            Err(
                '',
                [
                    {
                        'kind': 'unexpected_positional_argument',
                        'loc': [3],
                        'message': 'Unexpected positional argument',
                        'input_value': 4,
                    },
                    {
                        'kind': 'unexpected_positional_argument',
                        'loc': [4],
                        'message': 'Unexpected positional argument',
                        'input_value': 5,
                    },
                ],
            ),
        ],
        [
            (('x', 'a', 'wrong'), None),
            Err(
                '',
                [
                    {
                        'kind': 'int_parsing',
                        'loc': [0],
                        'message': 'Input should be a valid integer, unable to parse string as an integer',
                        'input_value': 'x',
                    },
                    {
                        'kind': 'bool_parsing',
                        'loc': [2],
                        'message': 'Input should be a valid boolean, unable to interpret input',
                        'input_value': 'wrong',
                    },
                ],
            ),
        ],
        [
            (None, None),
            Err(
                '3 validation errors for arguments',
                [
                    {
                        'kind': 'missing_positional_argument',
                        'loc': [0],
                        'message': 'Missing required positional argument',
                        'input_value': IsListOrTuple(None, None),
                    },
                    {
                        'kind': 'missing_positional_argument',
                        'loc': [1],
                        'message': 'Missing required positional argument',
                        'input_value': IsListOrTuple(None, None),
                    },
                    {
                        'kind': 'missing_positional_argument',
                        'loc': [2],
                        'message': 'Missing required positional argument',
                        'input_value': IsListOrTuple(None, None),
                    },
                ],
            ),
        ],
    ],
    ids=repr,
)
def test_positional_args(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [
                {'name': 'a', 'mode': 'positional_only', 'schema': 'int'},
                {'name': 'b', 'mode': 'positional_only', 'schema': 'str'},
                {'name': 'c', 'mode': 'positional_only', 'schema': 'bool'},
            ],
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)
        # debug(exc_info.value.errors())
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_test(input_value) == expected

    with pytest.raises(ValidationError, match='kind=arguments_type,'):
        # lists are not allowed from python, but no equivalent restriction in JSON
        v.validate_python([(1, 'a', True), None])


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [(None, {'a': 1, 'b': 'a', 'c': True}), ((), {'a': 1, 'b': 'a', 'c': True})],
        [{'a': 1, 'b': 'a', 'c': True}, ((), {'a': 1, 'b': 'a', 'c': True})],
        [(None, {'a': '1', 'b': 'a', 'c': 'True'}), ((), {'a': 1, 'b': 'a', 'c': True})],
        [((), {'a': 1, 'b': 'a', 'c': True}), ((), {'a': 1, 'b': 'a', 'c': True})],
        [((1,), {'a': 1, 'b': 'a', 'c': True}), Err('kind=unexpected_positional_argument,')],
        [
            ((), {'a': 1, 'b': 'a', 'c': True, 'd': 'wrong'}),
            Err(
                'kind=unexpected_keyword_argument,',
                [
                    {
                        'kind': 'unexpected_keyword_argument',
                        'loc': ['d'],
                        'message': 'Unexpected keyword argument',
                        'input_value': 'wrong',
                    }
                ],
            ),
        ],
        [
            ([], {'a': 1, 'b': 'a'}),
            Err(
                'kind=missing_keyword_argument,',
                [
                    {
                        'kind': 'missing_keyword_argument',
                        'loc': ['c'],
                        'message': 'Missing required keyword argument',
                        'input_value': IsListOrTuple([], {'a': 1, 'b': 'a'}),
                    }
                ],
            ),
        ],
        [
            ((), {'a': 'x', 'b': 'a', 'c': 'wrong'}),
            Err(
                '',
                [
                    {
                        'kind': 'int_parsing',
                        'loc': ['a'],
                        'message': 'Input should be a valid integer, unable to parse string as an integer',
                        'input_value': 'x',
                    },
                    {
                        'kind': 'bool_parsing',
                        'loc': ['c'],
                        'message': 'Input should be a valid boolean, unable to interpret input',
                        'input_value': 'wrong',
                    },
                ],
            ),
        ],
        [
            (None, None),
            Err(
                '',
                [
                    {
                        'kind': 'missing_keyword_argument',
                        'loc': ['a'],
                        'message': 'Missing required keyword argument',
                        'input_value': IsListOrTuple(None, None),
                    },
                    {
                        'kind': 'missing_keyword_argument',
                        'loc': ['b'],
                        'message': 'Missing required keyword argument',
                        'input_value': IsListOrTuple(None, None),
                    },
                    {
                        'kind': 'missing_keyword_argument',
                        'loc': ['c'],
                        'message': 'Missing required keyword argument',
                        'input_value': IsListOrTuple(None, None),
                    },
                ],
            ),
        ],
    ],
    ids=repr,
)
def test_keyword_args(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [
                {'name': 'a', 'mode': 'keyword_only', 'schema': 'int'},
                {'name': 'b', 'mode': 'keyword_only', 'schema': 'str'},
                {'name': 'c', 'mode': 'keyword_only', 'schema': 'bool'},
            ],
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)
        # debug(exc_info.value.errors())
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [(None, {'a': 1, 'b': 'bb', 'c': True}), ((), {'a': 1, 'b': 'bb', 'c': True})],
        [((1, 'bb'), {'c': True}), ((1, 'bb'), {'c': True})],
        [((1,), {'b': 'bb', 'c': True}), ((1,), {'b': 'bb', 'c': True})],
        [
            ((1,), {'a': 11, 'b': 'bb', 'c': True}),
            Err(
                'kind=multiple_argument_values,',
                [
                    {
                        'kind': 'multiple_argument_values',
                        'loc': ['a'],
                        'message': 'Got multiple values for argument',
                        'input_value': 11,
                    }
                ],
            ),
        ],
        [
            ([1, 'bb', 'cc'], {'b': 'bb', 'c': True}),
            Err(
                'kind=unexpected_positional_argument,',
                [
                    {
                        'kind': 'multiple_argument_values',
                        'loc': ['b'],
                        'message': 'Got multiple values for argument',
                        'input_value': 'bb',
                    },
                    {
                        'kind': 'unexpected_positional_argument',
                        'loc': [2],
                        'message': 'Unexpected positional argument',
                        'input_value': 'cc',
                    },
                ],
            ),
        ],
        [
            ((1, 'b1'), {'a': 11, 'b': 'b2', 'c': True}),
            Err(
                'kind=multiple_argument_values,',
                [
                    {
                        'kind': 'multiple_argument_values',
                        'loc': ['a'],
                        'message': 'Got multiple values for argument',
                        'input_value': 11,
                    },
                    {
                        'kind': 'multiple_argument_values',
                        'loc': ['b'],
                        'message': 'Got multiple values for argument',
                        'input_value': 'b2',
                    },
                ],
            ),
        ],
    ],
    ids=repr,
)
def test_positional_or_keyword(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [
                {'name': 'a', 'mode': 'positional_or_keyword', 'schema': 'int'},
                {'name': 'b', 'schema': 'str'},  # default mode is positional_or_keyword
                {'name': 'c', 'mode': 'keyword_only', 'schema': 'bool'},
            ],
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)
        # debug(exc_info.value.errors())
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize('input_value,expected', [[((1,), None), ((1,), {})], [((), None), ((42,), {})]], ids=repr)
def test_positional_optional(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [{'name': 'a', 'mode': 'positional_only', 'schema': 'int', 'default': 42}],
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)
        # debug(exc_info.value.errors())
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [(None, {'a': 1}), ((), {'a': 1})],
        [(None, None), ((), {'a': 1})],
        [((), {'a': 1}), ((), {'a': 1})],
        [((), None), ((), {'a': 1})],
    ],
    ids=repr,
)
def test_p_or_k_optional(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [{'name': 'a', 'mode': 'positional_or_keyword', 'schema': 'int', 'default': 1}],
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)
        # debug(exc_info.value.errors())
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [([1, 2, 3], None), ((1, 2, 3), {})],
        [([1], None), ((1,), {})],
        [([], None), ((), {})],
        [([], {}), ((), {})],
        [([1, 2, 3], {'a': 1}), Err('a\n  Unexpected keyword argument [kind=unexpected_keyword_argument,')],
    ],
    ids=repr,
)
def test_var_args_only(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'arguments', 'arguments_schema': [], 'var_args_schema': 'int'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)
        # debug(exc_info.value.errors())
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [([1, 2, 3], None), ((1, 2, 3), {})],
        [(['1', '2', '3'], None), ((1, 2, 3), {})],
        [([1], None), ((1,), {})],
        [([], None), Err('0\n  Missing required positional argument')],
        [
            (['x'], None),
            Err(
                'kind=int_parsing,',
                [
                    {
                        'kind': 'int_parsing',
                        'loc': [0],
                        'message': 'Input should be a valid integer, unable to parse string as an integer',
                        'input_value': 'x',
                    }
                ],
            ),
        ],
        [
            ([1, 'x', 'y'], None),
            Err(
                'kind=int_parsing,',
                [
                    {
                        'kind': 'int_parsing',
                        'loc': [1],
                        'message': 'Input should be a valid integer, unable to parse string as an integer',
                        'input_value': 'x',
                    },
                    {
                        'kind': 'int_parsing',
                        'loc': [2],
                        'message': 'Input should be a valid integer, unable to parse string as an integer',
                        'input_value': 'y',
                    },
                ],
            ),
        ],
        [([1, 2, 3], {'a': 1}), Err('a\n  Unexpected keyword argument [kind=unexpected_keyword_argument,')],
    ],
    ids=repr,
)
def test_args_var_args_only(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [{'name': 'a', 'mode': 'positional_only', 'schema': 'int'}],
            'var_args_schema': 'int',
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)
        # debug(exc_info.value.errors())
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [([1, 'a', 'true'], {'b': 'bb', 'c': 3}), ((1, 'a', True), {'b': 'bb', 'c': 3})],
        [([1, 'a'], {'a': 'true', 'b': 'bb', 'c': 3}), ((1, 'a'), {'a': True, 'b': 'bb', 'c': 3})],
        [
            ([1, 'a', 'true', 4, 5], {'b': 'bb', 'c': 3}),
            Err(
                'kind=unexpected_positional_argument,',
                [
                    {
                        'kind': 'unexpected_positional_argument',
                        'loc': [3],
                        'message': 'Unexpected positional argument',
                        'input_value': 4,
                    },
                    {
                        'kind': 'unexpected_positional_argument',
                        'loc': [4],
                        'message': 'Unexpected positional argument',
                        'input_value': 5,
                    },
                ],
            ),
        ],
    ],
    ids=repr,
)
def test_both(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [
                {'name': '1', 'mode': 'positional_only', 'schema': 'int'},
                {'name': '2', 'mode': 'positional_only', 'schema': 'str'},
                {'name': 'a', 'mode': 'positional_or_keyword', 'schema': 'bool'},
                {'name': 'b', 'mode': 'keyword_only', 'schema': 'str'},
                {'name': 'c', 'mode': 'keyword_only', 'schema': 'int'},
            ],
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [([], {}), ((), {})],
        [(None, None), ((), {})],
        [(None, {}), ((), {})],
        [([], None), ((), {})],
        [([1], None), Err('0\n  Unexpected positional argument [kind=unexpected_positional_argument,')],
        [([], {'a': 1}), Err('a\n  Unexpected keyword argument [kind=unexpected_keyword_argument,')],
        [
            ([1], {'a': 2}),
            Err(
                '[kind=unexpected_keyword_argument,',
                [
                    {
                        'kind': 'unexpected_positional_argument',
                        'loc': [0],
                        'message': 'Unexpected positional argument',
                        'input_value': 1,
                    },
                    {
                        'kind': 'unexpected_keyword_argument',
                        'loc': ['a'],
                        'message': 'Unexpected keyword argument',
                        'input_value': 2,
                    },
                ],
            ),
        ],
    ],
    ids=repr,
)
def test_no_args(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'arguments', 'arguments_schema': []})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)
        # debug(exc_info.value.errors())
        if expected.errors is not None:
            assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_test(input_value) == expected


def double_or_bust(input_value, **kwargs):
    if input_value == 1:
        raise RuntimeError('bust')
    return input_value * 2


def test_internal_error(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [
                {'name': 'a', 'mode': 'positional_only', 'schema': 'int'},
                {
                    'name': 'b',
                    'mode': 'positional_only',
                    'schema': {'type': 'function', 'mode': 'plain', 'function': double_or_bust},
                },
            ],
        }
    )
    assert v.validate_test(((1, 2), None)) == ((1, 4), {})
    with pytest.raises(RuntimeError, match='bust'):
        v.validate_test(((1, 1), None))


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [((1, 2), None), ((1, 2), {})],
        [((1,), None), ((1,), {'b': 42})],
        [((1,), {'b': 3}), ((1,), {'b': 3})],
        [(None, {'a': 1}), ((), {'a': 1, 'b': 42})],
    ],
    ids=repr,
)
def test_default_factory(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [
                {'name': 'a', 'mode': 'positional_or_keyword', 'schema': 'int'},
                {'name': 'b', 'mode': 'positional_or_keyword', 'schema': 'int', 'default_factory': lambda: 42},
            ],
        }
    )
    assert v.validate_test(input_value) == expected


def test_repr():
    v = SchemaValidator(
        {
            'type': 'arguments',
            'arguments_schema': [
                {'name': 'b', 'mode': 'positional_or_keyword', 'schema': 'int'},
                {'name': 'a', 'mode': 'keyword_only', 'schema': 'int', 'default_factory': lambda: 42},
            ],
        }
    )
    assert 'positional_params_count:1,' in plain_repr(v)


def test_build_non_default_follows():
    with pytest.raises(SchemaError, match='Non-default argument follows default argument'):
        SchemaValidator(
            {
                'type': 'arguments',
                'arguments_schema': [
                    {'name': 'a', 'mode': 'positional_or_keyword', 'schema': 'int', 'default_factory': lambda: 42},
                    {'name': 'b', 'mode': 'positional_or_keyword', 'schema': 'int'},
                ],
            }
        )


def test_build_default_and_default_factory():
    with pytest.raises(SchemaError, match="'default' and 'default_factory' cannot be used together"):
        SchemaValidator(
            {
                'type': 'arguments',
                'arguments_schema': [
                    {
                        'name': 'a',
                        'mode': 'positional_or_keyword',
                        'schema': 'int',
                        'default_factory': lambda: 1,
                        'default': 2,
                    }
                ],
            }
        )


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [((1, 2), None), ((1, 2), {})],
        [((1,), {'b': '4', 'c': 'a'}), ((1,), {'b': 4, 'c': 'a'})],
        [((1, 2), {'x': 'abc'}), ((1, 2), {'x': 'abc'})],
    ],
    ids=repr,
)
def test_kwargs(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [
                {'name': 'a', 'mode': 'positional_only', 'schema': 'int'},
                {'name': 'b', 'mode': 'positional_or_keyword', 'schema': 'int'},
            ],
            'var_kwargs_schema': 'str',
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [((1,), None), ((1,), {})],
        [(None, {'Foo': 1}), ((), {'a': 1})],
        [(None, {'a': 1}), Err('a\n  Missing required keyword argument [kind=missing_keyword_argument,')],
    ],
    ids=repr,
)
def test_alias(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [{'name': 'a', 'mode': 'positional_or_keyword', 'schema': 'int', 'alias': 'Foo'}],
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [((1,), None), ((1,), {})],
        [(None, {'Foo': 1}), ((), {'a': 1})],
        [(None, {'a': 1}), ((), {'a': 1})],
        [(None, {'a': 1, 'b': 2}), Err('b\n  Unexpected keyword argument [kind=unexpected_keyword_argument,')],
        [(None, {'a': 1, 'Foo': 2}), Err('a\n  Unexpected keyword argument [kind=unexpected_keyword_argument,')],
    ],
    ids=repr,
)
def test_alias_populate_by_name(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [{'name': 'a', 'mode': 'positional_or_keyword', 'schema': 'int', 'alias': 'Foo'}],
            'populate_by_name': True,
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


def validate(function):
    """
    a demo validation decorator to test arguments
    """
    parameters = signature(function).parameters

    type_hints = get_type_hints(function)
    mode_lookup = {
        Parameter.POSITIONAL_ONLY: 'positional_only',
        Parameter.POSITIONAL_OR_KEYWORD: 'positional_or_keyword',
        Parameter.KEYWORD_ONLY: 'keyword_only',
    }

    arguments_schema = []
    schema = {'type': 'arguments', 'arguments_schema': arguments_schema}
    for i, (name, p) in enumerate(parameters.items()):
        if p.annotation is p.empty:
            annotation = Any
        else:
            annotation = type_hints[name]

        assert annotation in (bool, int, float, str, Any), f'schema for {annotation} not implemented'
        if annotation in (bool, int, float, str):
            arg_schema = annotation.__name__
        else:
            assert annotation is Any
            arg_schema = 'any'

        if p.kind in mode_lookup:
            s = {'name': name, 'mode': mode_lookup[p.kind], 'schema': arg_schema}
            if p.default is not p.empty:
                s['default'] = p.default
            arguments_schema.append(s)
        elif p.kind == Parameter.VAR_POSITIONAL:
            schema['var_args_schema'] = arg_schema
        else:
            assert p.kind == Parameter.VAR_KEYWORD, p.kind
            schema['var_kwargs_schema'] = arg_schema

    validator = SchemaValidator(schema)

    @wraps(function)
    def wrapper(*args, **kwargs):
        validated_args, validated_kwargs = validator.validate_python((args, kwargs))
        return function(*validated_args, **validated_kwargs)

    return wrapper


def test_function_any():
    @validate
    def foobar(a, b, c):
        return a, b, c

    assert foobar(1, 2, 3) == (1, 2, 3)
    assert foobar(1, 2, 3) == (1, 2, 3)
    assert foobar(a=1, b=2, c=3) == (1, 2, 3)
    assert foobar(1, b=2, c=3) == (1, 2, 3)

    with pytest.raises(ValidationError, match='Unexpected positional argument'):
        foobar(1, 2, 3, 4)

    with pytest.raises(ValidationError, match='d\n  Unexpected keyword argument'):
        foobar(1, 2, 3, d=4)


def test_function_types():
    @validate
    def foobar(a: int, b: int, *, c: int):
        return a, b, c

    assert foobar(1, 2, c='3') == (1, 2, 3)
    assert foobar(a=1, b='2', c=3) == (1, 2, 3)

    with pytest.raises(ValidationError, match='Unexpected positional argument'):
        foobar(1, 2, 3)

    with pytest.raises(ValidationError) as exc_info:
        foobar(1, 'b')

    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': [1],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'b',
        },
        {
            'kind': 'missing_keyword_argument',
            'loc': ['c'],
            'message': 'Missing required keyword argument',
            'input_value': ((1, 'b'), {}),
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        foobar(1, 'b', c='c')

    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': [1],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'b',
        },
        {
            'kind': 'int_parsing',
            'loc': ['c'],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'c',
        },
    ]


@pytest.mark.skipif(sys.version_info < (3, 10), reason='requires python3.10 or higher')
def test_function_positional_only(import_execute):
    # language=Python
    m = import_execute(
        """
def create_function(validate):
    @validate
    def foobar(a: int, b: int, /, c: int):
        return a, b, c
    return foobar
"""
    )
    foobar = m.create_function(validate)
    assert foobar('1', 2, 3) == (1, 2, 3)
    assert foobar('1', 2, c=3) == (1, 2, 3)
    with pytest.raises(ValidationError) as exc_info:
        foobar('1', b=2, c=3)
    assert exc_info.value.errors() == [
        {
            'kind': 'missing_positional_argument',
            'loc': [1],
            'message': 'Missing required positional argument',
            'input_value': (('1',), {'b': 2, 'c': 3}),
        },
        {
            'kind': 'unexpected_keyword_argument',
            'loc': ['b'],
            'message': 'Unexpected keyword argument',
            'input_value': 2,
        },
    ]


@pytest.mark.skipif(sys.version_info < (3, 10), reason='requires python3.10 or higher')
def test_function_positional_only_default(import_execute):
    # language=Python
    m = import_execute(
        """
def create_function(validate):
    @validate
    def foobar(a: int, b: int = 42, /):
        return a, b
    return foobar
"""
    )
    foobar = m.create_function(validate)
    assert foobar('1', 2) == (1, 2)
    assert foobar('1') == (1, 42)


@pytest.mark.skipif(sys.version_info < (3, 10), reason='requires python3.10 or higher')
def test_function_positional_kwargs(import_execute):
    # language=Python
    m = import_execute(
        """
def create_function(validate):
    @validate
    def foobar(a: int, b: int, /, **kwargs: bool):
        return a, b, kwargs
    return foobar
"""
    )
    foobar = m.create_function(validate)
    assert foobar('1', 2) == (1, 2, {})
    assert foobar('1', 2, c=True) == (1, 2, {'c': True})
    assert foobar('1', 2, a='false') == (1, 2, {'a': False})


def test_function_args_kwargs():
    @validate
    def foobar(*args, **kwargs):
        return args, kwargs

    assert foobar(1, 2, 3, a=4, b=5) == ((1, 2, 3), {'a': 4, 'b': 5})
    assert foobar(1, 2, 3) == ((1, 2, 3), {})
    assert foobar(a=1, b=2, c=3) == ((), {'a': 1, 'b': 2, 'c': 3})
    assert foobar() == ((), {})
