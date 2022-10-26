import re
import sys
from functools import wraps
from inspect import Parameter, signature
from typing import Any, get_type_hints

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError

from ..conftest import Err, PyAndJson, plain_repr


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [(1, 'a', True), ((1, 'a', True), {})],
        [[1, 'a', True], ((1, 'a', True), {})],
        [{'__args__': (1, 'a', True), '__kwargs__': {}}, ((1, 'a', True), {})],
        [[1, 'a', True], ((1, 'a', True), {})],
        [(1, 'a', 'true'), ((1, 'a', True), {})],
        ['x', Err('type=arguments_type,')],
        [
            {'__args__': (1, 'a', True), '__kwargs__': ()},
            Err('Keyword arguments must be a dictionary [type=keyword_arguments_type,'),
        ],
        [
            {'__args__': {}, '__kwargs__': {}},
            Err('Positional arguments must be a list or tuple [type=positional_arguments_type,'),
        ],
        [
            {'__args__': [1, 'a', True], '__kwargs__': {'x': 1}},
            Err(
                '',
                [
                    {
                        'type': 'unexpected_keyword_argument',
                        'loc': ('x',),
                        'msg': 'Unexpected keyword argument',
                        'input': 1,
                    }
                ],
            ),
        ],
        [
            [1],
            Err(
                '',
                [
                    {
                        'type': 'missing_positional_argument',
                        'loc': (1,),
                        'msg': 'Missing required positional argument',
                        'input': [1],
                    },
                    {
                        'type': 'missing_positional_argument',
                        'loc': (2,),
                        'msg': 'Missing required positional argument',
                        'input': [1],
                    },
                ],
            ),
        ],
        [
            [1, 'a', True, 4],
            Err(
                '',
                [
                    {
                        'type': 'unexpected_positional_argument',
                        'loc': (3,),
                        'msg': 'Unexpected positional argument',
                        'input': 4,
                    }
                ],
            ),
        ],
        [
            [1, 'a', True, 4, 5],
            Err(
                '',
                [
                    {
                        'type': 'unexpected_positional_argument',
                        'loc': (3,),
                        'msg': 'Unexpected positional argument',
                        'input': 4,
                    },
                    {
                        'type': 'unexpected_positional_argument',
                        'loc': (4,),
                        'msg': 'Unexpected positional argument',
                        'input': 5,
                    },
                ],
            ),
        ],
        [
            ('x', 'a', 'wrong'),
            Err(
                '',
                [
                    {
                        'type': 'int_parsing',
                        'loc': (0,),
                        'msg': 'Input should be a valid integer, unable to parse string as an integer',
                        'input': 'x',
                    },
                    {
                        'type': 'bool_parsing',
                        'loc': (2,),
                        'msg': 'Input should be a valid boolean, unable to interpret input',
                        'input': 'wrong',
                    },
                ],
            ),
        ],
        [
            {'__args__': None, '__kwargs__': None},
            Err(
                '3 validation errors for arguments',
                [
                    {
                        'type': 'missing_positional_argument',
                        'loc': (0,),
                        'msg': 'Missing required positional argument',
                        'input': {'__args__': None, '__kwargs__': None},
                    },
                    {
                        'type': 'missing_positional_argument',
                        'loc': (1,),
                        'msg': 'Missing required positional argument',
                        'input': {'__args__': None, '__kwargs__': None},
                    },
                    {
                        'type': 'missing_positional_argument',
                        'loc': (2,),
                        'msg': 'Missing required positional argument',
                        'input': {'__args__': None, '__kwargs__': None},
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
                {'name': 'a', 'mode': 'positional_only', 'schema': {'type': 'int'}},
                {'name': 'b', 'mode': 'positional_only', 'schema': {'type': 'str'}},
                {'name': 'c', 'mode': 'positional_only', 'schema': {'type': 'bool'}},
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
        [{'__args__': None, '__kwargs__': {'a': 1, 'b': 'a', 'c': True}}, ((), {'a': 1, 'b': 'a', 'c': True})],
        [{'a': 1, 'b': 'a', 'c': True}, ((), {'a': 1, 'b': 'a', 'c': True})],
        [{'__args__': None, '__kwargs__': {'a': '1', 'b': 'a', 'c': 'True'}}, ((), {'a': 1, 'b': 'a', 'c': True})],
        [{'__args__': (), '__kwargs__': {'a': 1, 'b': 'a', 'c': True}}, ((), {'a': 1, 'b': 'a', 'c': True})],
        [{'__args__': (1,), '__kwargs__': {'a': 1, 'b': 'a', 'c': True}}, Err('type=unexpected_positional_argument,')],
        [
            {'__args__': (), '__kwargs__': {'a': 1, 'b': 'a', 'c': True, 'd': 'wrong'}},
            Err(
                'type=unexpected_keyword_argument,',
                [
                    {
                        'type': 'unexpected_keyword_argument',
                        'loc': ('d',),
                        'msg': 'Unexpected keyword argument',
                        'input': 'wrong',
                    }
                ],
            ),
        ],
        [
            {'__args__': [], '__kwargs__': {'a': 1, 'b': 'a'}},
            Err(
                'type=missing_keyword_argument,',
                [
                    {
                        'type': 'missing_keyword_argument',
                        'loc': ('c',),
                        'msg': 'Missing required keyword argument',
                        'input': {'__args__': [], '__kwargs__': {'a': 1, 'b': 'a'}},
                    }
                ],
            ),
        ],
        [
            {'__args__': (), '__kwargs__': {'a': 'x', 'b': 'a', 'c': 'wrong'}},
            Err(
                '',
                [
                    {
                        'type': 'int_parsing',
                        'loc': ('a',),
                        'msg': 'Input should be a valid integer, unable to parse string as an integer',
                        'input': 'x',
                    },
                    {
                        'type': 'bool_parsing',
                        'loc': ('c',),
                        'msg': 'Input should be a valid boolean, unable to interpret input',
                        'input': 'wrong',
                    },
                ],
            ),
        ],
        [
            {'__args__': None, '__kwargs__': None},
            Err(
                '',
                [
                    {
                        'type': 'missing_keyword_argument',
                        'loc': ('a',),
                        'msg': 'Missing required keyword argument',
                        'input': {'__args__': None, '__kwargs__': None},
                    },
                    {
                        'type': 'missing_keyword_argument',
                        'loc': ('b',),
                        'msg': 'Missing required keyword argument',
                        'input': {'__args__': None, '__kwargs__': None},
                    },
                    {
                        'type': 'missing_keyword_argument',
                        'loc': ('c',),
                        'msg': 'Missing required keyword argument',
                        'input': {'__args__': None, '__kwargs__': None},
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
                {'name': 'a', 'mode': 'keyword_only', 'schema': {'type': 'int'}},
                {'name': 'b', 'mode': 'keyword_only', 'schema': {'type': 'str'}},
                {'name': 'c', 'mode': 'keyword_only', 'schema': {'type': 'bool'}},
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
        [{'a': 1, 'b': 'bb', 'c': True}, ((), {'a': 1, 'b': 'bb', 'c': True})],
        [{'__args__': None, '__kwargs__': {'a': 1, 'b': 'bb', 'c': True}}, ((), {'a': 1, 'b': 'bb', 'c': True})],
        [{'__args__': (1, 'bb'), '__kwargs__': {'c': True}}, ((1, 'bb'), {'c': True})],
        [{'__args__': (1,), '__kwargs__': {'b': 'bb', 'c': True}}, ((1,), {'b': 'bb', 'c': True})],
        [
            {'__args__': (1,), '__kwargs__': {'a': 11, 'b': 'bb', 'c': True}},
            Err(
                'type=multiple_argument_values,',
                [
                    {
                        'type': 'multiple_argument_values',
                        'loc': ('a',),
                        'msg': 'Got multiple values for argument',
                        'input': 11,
                    }
                ],
            ),
        ],
        [
            {'__args__': [1, 'bb', 'cc'], '__kwargs__': {'b': 'bb', 'c': True}},
            Err(
                'type=unexpected_positional_argument,',
                [
                    {
                        'type': 'multiple_argument_values',
                        'loc': ('b',),
                        'msg': 'Got multiple values for argument',
                        'input': 'bb',
                    },
                    {
                        'type': 'unexpected_positional_argument',
                        'loc': (2,),
                        'msg': 'Unexpected positional argument',
                        'input': 'cc',
                    },
                ],
            ),
        ],
        [
            {'__args__': (1, 'b1'), '__kwargs__': {'a': 11, 'b': 'b2', 'c': True}},
            Err(
                'type=multiple_argument_values,',
                [
                    {
                        'type': 'multiple_argument_values',
                        'loc': ('a',),
                        'msg': 'Got multiple values for argument',
                        'input': 11,
                    },
                    {
                        'type': 'multiple_argument_values',
                        'loc': ('b',),
                        'msg': 'Got multiple values for argument',
                        'input': 'b2',
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
                {'name': 'a', 'mode': 'positional_or_keyword', 'schema': {'type': 'int'}},
                {'name': 'b', 'schema': {'type': 'str'}},  # default mode is positional_or_keyword
                {'name': 'c', 'mode': 'keyword_only', 'schema': {'type': 'bool'}},
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


@pytest.mark.parametrize('input_value,expected', [[(1,), ((1,), {})], [(), ((42,), {})]], ids=repr)
def test_positional_optional(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [
                {
                    'name': 'a',
                    'mode': 'positional_only',
                    'schema': {'type': 'default', 'schema': {'type': 'int'}, 'default': 42},
                }
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
        [{'a': 1}, ((), {'a': 1})],
        [{'__args__': None, '__kwargs__': {'a': 1}}, ((), {'a': 1})],
        [{'__args__': None, '__kwargs__': None}, ((), {'a': 1})],
        [{'__args__': (), '__kwargs__': {'a': 1}}, ((), {'a': 1})],
        [{'__args__': (), '__kwargs__': None}, ((), {'a': 1})],
    ],
    ids=repr,
)
def test_p_or_k_optional(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [
                {
                    'name': 'a',
                    'mode': 'positional_or_keyword',
                    'schema': {'type': 'default', 'schema': {'type': 'int'}, 'default': 1},
                }
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
        [[1, 2, 3], ((1, 2, 3), {})],
        [{'__args__': [1, 2, 3], '__kwargs__': None}, ((1, 2, 3), {})],
        [[1], ((1,), {})],
        [[], ((), {})],
        [{'__args__': [], '__kwargs__': {}}, ((), {})],
        [
            {'__args__': [1, 2, 3], '__kwargs__': {'a': 1}},
            Err('a\n  Unexpected keyword argument [type=unexpected_keyword_argument,'),
        ],
    ],
    ids=repr,
)
def test_var_args_only(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'arguments', 'arguments_schema': [], 'var_args_schema': {'type': 'int'}})
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
        [[1, 2, 3], ((1, 2, 3), {})],
        [['1', '2', '3'], ((1, 2, 3), {})],
        [[1], ((1,), {})],
        [[], Err('0\n  Missing required positional argument')],
        [
            ['x'],
            Err(
                'type=int_parsing,',
                [
                    {
                        'type': 'int_parsing',
                        'loc': (0,),
                        'msg': 'Input should be a valid integer, unable to parse string as an integer',
                        'input': 'x',
                    }
                ],
            ),
        ],
        [
            [1, 'x', 'y'],
            Err(
                'type=int_parsing,',
                [
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
                ],
            ),
        ],
        [
            {'__args__': [1, 2, 3], '__kwargs__': {'a': 1}},
            Err('a\n  Unexpected keyword argument [type=unexpected_keyword_argument,'),
        ],
    ],
    ids=repr,
)
def test_args_var_args_only(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [{'name': 'a', 'mode': 'positional_only', 'schema': {'type': 'int'}}],
            'var_args_schema': {'type': 'int'},
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
        [{'__args__': [1, 'a', 'true'], '__kwargs__': {'b': 'bb', 'c': 3}}, ((1, 'a', True), {'b': 'bb', 'c': 3})],
        [
            {'__args__': [1, 'a'], '__kwargs__': {'a': 'true', 'b': 'bb', 'c': 3}},
            ((1, 'a'), {'a': True, 'b': 'bb', 'c': 3}),
        ],
        [
            {'__args__': [1, 'a', 'true', 4, 5], '__kwargs__': {'b': 'bb', 'c': 3}},
            Err(
                'type=unexpected_positional_argument,',
                [
                    {
                        'type': 'unexpected_positional_argument',
                        'loc': (3,),
                        'msg': 'Unexpected positional argument',
                        'input': 4,
                    },
                    {
                        'type': 'unexpected_positional_argument',
                        'loc': (4,),
                        'msg': 'Unexpected positional argument',
                        'input': 5,
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
                {'name': '1', 'mode': 'positional_only', 'schema': {'type': 'int'}},
                {'name': '2', 'mode': 'positional_only', 'schema': {'type': 'str'}},
                {'name': 'a', 'mode': 'positional_or_keyword', 'schema': {'type': 'bool'}},
                {'name': 'b', 'mode': 'keyword_only', 'schema': {'type': 'str'}},
                {'name': 'c', 'mode': 'keyword_only', 'schema': {'type': 'int'}},
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
        [{'__args__': [], '__kwargs__': {}}, ((), {})],
        [{'__args__': None, '__kwargs__': None}, ((), {})],
        [{'__args__': None, '__kwargs__': {}}, ((), {})],
        [[], ((), {})],
        [[1], Err('0\n  Unexpected positional argument [type=unexpected_positional_argument,')],
        [{'a': 1}, Err('a\n  Unexpected keyword argument [type=unexpected_keyword_argument,')],
        [
            {'__args__': [1], '__kwargs__': {'a': 2}},
            Err(
                '[type=unexpected_keyword_argument,',
                [
                    {
                        'type': 'unexpected_positional_argument',
                        'loc': (0,),
                        'msg': 'Unexpected positional argument',
                        'input': 1,
                    },
                    {
                        'type': 'unexpected_keyword_argument',
                        'loc': ('a',),
                        'msg': 'Unexpected keyword argument',
                        'input': 2,
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
                {'name': 'a', 'mode': 'positional_only', 'schema': {'type': 'int'}},
                {
                    'name': 'b',
                    'mode': 'positional_only',
                    'schema': {'type': 'function', 'mode': 'plain', 'function': double_or_bust},
                },
            ],
        }
    )
    assert v.validate_test((1, 2)) == ((1, 4), {})
    with pytest.raises(RuntimeError, match='bust'):
        v.validate_test((1, 1))


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [{'__args__': (1, 2), '__kwargs__': None}, ((1, 2), {})],
        [{'__args__': (1,), '__kwargs__': None}, ((1,), {'b': 42})],
        [{'__args__': (1,), '__kwargs__': {'b': 3}}, ((1,), {'b': 3})],
        [{'__args__': None, '__kwargs__': {'a': 1}}, ((), {'a': 1, 'b': 42})],
    ],
    ids=repr,
)
def test_default_factory(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [
                {'name': 'a', 'mode': 'positional_or_keyword', 'schema': {'type': 'int'}},
                {
                    'name': 'b',
                    'mode': 'positional_or_keyword',
                    'schema': {'type': 'default', 'schema': {'type': 'int'}, 'default_factory': lambda: 42},
                },
            ],
        }
    )
    assert v.validate_test(input_value) == expected


def test_repr():
    v = SchemaValidator(
        {
            'type': 'arguments',
            'arguments_schema': [
                {'name': 'b', 'mode': 'positional_or_keyword', 'schema': {'type': 'int'}},
                {
                    'name': 'a',
                    'mode': 'keyword_only',
                    'schema': {'type': 'default', 'schema': {'type': 'int'}, 'default_factory': lambda: 42},
                },
            ],
        }
    )
    assert 'positional_params_count:1,' in plain_repr(v)


def test_build_non_default_follows():
    with pytest.raises(SchemaError, match="Non-default argument 'b' follows default argument"):
        SchemaValidator(
            {
                'type': 'arguments',
                'arguments_schema': [
                    {
                        'name': 'a',
                        'mode': 'positional_or_keyword',
                        'schema': {'type': 'default', 'schema': {'type': 'int'}, 'default_factory': lambda: 42},
                    },
                    {'name': 'b', 'mode': 'positional_or_keyword', 'schema': {'type': 'int'}},
                ],
            }
        )


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [{'__args__': (1, 2), '__kwargs__': None}, ((1, 2), {})],
        [{'__args__': (1,), '__kwargs__': {'b': '4', 'c': 'a'}}, ((1,), {'b': 4, 'c': 'a'})],
        [{'__args__': (1, 2), '__kwargs__': {'x': 'abc'}}, ((1, 2), {'x': 'abc'})],
    ],
    ids=repr,
)
def test_kwargs(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [
                {'name': 'a', 'mode': 'positional_only', 'schema': {'type': 'int'}},
                {'name': 'b', 'mode': 'positional_or_keyword', 'schema': {'type': 'int'}},
            ],
            'var_kwargs_schema': {'type': 'str'},
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
        [{'__args__': [1, 2]}, ((), {'__args__': [1, 2]})],
        [{'__kwargs__': {'x': 'abc'}}, ((), {'__kwargs__': {'x': 'abc'}})],
        [
            {'__args__': [1, 2], '__kwargs__': {'x': 'abc'}, 'more': 'hello'},
            ((), {'__args__': [1, 2], '__kwargs__': {'x': 'abc'}, 'more': 'hello'}),
        ],
    ],
    ids=repr,
)
def test_var_kwargs(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'arguments', 'arguments_schema': [], 'var_kwargs_schema': {'type': 'any'}})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [{'__args__': (1,), '__kwargs__': None}, ((1,), {})],
        [{'__args__': None, '__kwargs__': {'Foo': 1}}, ((), {'a': 1})],
        [
            {'__args__': None, '__kwargs__': {'a': 1}},
            Err('a\n  Missing required keyword argument [type=missing_keyword_argument,'),
        ],
    ],
    ids=repr,
)
def test_alias(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [
                {'name': 'a', 'mode': 'positional_or_keyword', 'schema': {'type': 'int'}, 'alias': 'Foo'}
            ],
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
        [{'__args__': (1,), '__kwargs__': None}, ((1,), {})],
        [{'__args__': None, '__kwargs__': {'Foo': 1}}, ((), {'a': 1})],
        [{'__args__': None, '__kwargs__': {'a': 1}}, ((), {'a': 1})],
        [
            {'__args__': None, '__kwargs__': {'a': 1, 'b': 2}},
            Err('b\n  Unexpected keyword argument [type=unexpected_keyword_argument,'),
        ],
        [
            {'__args__': None, '__kwargs__': {'a': 1, 'Foo': 2}},
            Err('a\n  Unexpected keyword argument [type=unexpected_keyword_argument,'),
        ],
    ],
    ids=repr,
)
def test_alias_populate_by_name(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'arguments',
            'arguments_schema': [
                {'name': 'a', 'mode': 'positional_or_keyword', 'schema': {'type': 'int'}, 'alias': 'Foo'}
            ],
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
            arg_schema = {'type': annotation.__name__}
        else:
            assert annotation is Any
            arg_schema = {'type': 'any'}

        if p.kind in mode_lookup:
            if p.default is not p.empty:
                arg_schema = {'type': 'default', 'schema': arg_schema, 'default': p.default}
            s = {'name': name, 'mode': mode_lookup[p.kind], 'schema': arg_schema}
            arguments_schema.append(s)
        elif p.kind == Parameter.VAR_POSITIONAL:
            schema['var_args_schema'] = arg_schema
        else:
            assert p.kind == Parameter.VAR_KEYWORD, p.kind
            schema['var_kwargs_schema'] = arg_schema

    validator = SchemaValidator(schema)

    @wraps(function)
    def wrapper(*args, **kwargs):
        validated_args, validated_kwargs = validator.validate_python({'__args__': args, '__kwargs__': kwargs})
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
            'type': 'int_parsing',
            'loc': (1,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'b',
        },
        {
            'type': 'missing_keyword_argument',
            'loc': ('c',),
            'msg': 'Missing required keyword argument',
            'input': {'__args__': (1, 'b'), '__kwargs__': {}},
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        foobar(1, 'b', c='c')

    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': (1,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'b',
        },
        {
            'type': 'int_parsing',
            'loc': ('c',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'c',
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
            'type': 'missing_positional_argument',
            'loc': (1,),
            'msg': 'Missing required positional argument',
            'input': {'__args__': ('1',), '__kwargs__': {'b': 2, 'c': 3}},
        },
        {'type': 'unexpected_keyword_argument', 'loc': ('b',), 'msg': 'Unexpected keyword argument', 'input': 2},
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


def test_invalid_schema():
    with pytest.raises(SchemaError, match="'default' and 'default_factory' cannot be used together"):
        SchemaValidator(
            {
                'type': 'arguments',
                'arguments_schema': [
                    {
                        'name': 'a',
                        'mode': 'positional_or_keyword',
                        'schema': {
                            'type': 'default',
                            'schema': {'type': 'int'},
                            'default': 1,
                            'default_factory': lambda: 2,
                        },
                    }
                ],
            }
        )
