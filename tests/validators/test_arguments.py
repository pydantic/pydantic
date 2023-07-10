import re
import sys
from functools import wraps
from inspect import Parameter, signature
from typing import Any, get_type_hints

import pytest

from pydantic_core import ArgsKwargs, SchemaError, SchemaValidator, ValidationError, core_schema

from ..conftest import Err, PyAndJson, plain_repr


def test_args_kwargs():
    ak = ArgsKwargs(('hello', True))
    assert str(ak) == "ArgsKwargs(('hello', True))"
    assert repr(ak) == "ArgsKwargs(('hello', True))"
    assert ak.args == ('hello', True)
    assert ak.kwargs is None
    ak2 = ArgsKwargs((), {'a': 123})
    assert repr(ak2) == "ArgsKwargs((), {'a': 123})"
    assert ak2.args == ()
    assert ak2.kwargs == {'a': 123}
    ak3 = ArgsKwargs(('hello', True), {'a': 123, 'b': b'bytes'})
    assert repr(ak3) == "ArgsKwargs(('hello', True), {'a': 123, 'b': b'bytes'})"

    assert ak != ak2

    assert ak == ArgsKwargs(('hello', True))
    assert ak3 == ArgsKwargs(('hello', True), {'a': 123, 'b': b'bytes'})
    assert ak3 != ArgsKwargs(('hello', True), {'a': 123, 'b': b'different'})
    assert ArgsKwargs((1,), {}) == ArgsKwargs((1,), None) == ArgsKwargs((1,))

    assert repr(ArgsKwargs((1,))) == 'ArgsKwargs((1,))'


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [(1, 'a', True), ((1, 'a', True), {})],
        [[1, 'a', True], ((1, 'a', True), {})],
        [ArgsKwargs((1, 'a', True)), ((1, 'a', True), {})],
        [(1, 'a', 'true'), ((1, 'a', True), {})],
        ['x', Err('type=arguments_type,')],
        [
            ArgsKwargs((1, 'a', True), {'x': 1}),
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
                        'type': 'missing_positional_only_argument',
                        'loc': (1,),
                        'msg': 'Missing required positional only argument',
                        'input': [1],
                    },
                    {
                        'type': 'missing_positional_only_argument',
                        'loc': (2,),
                        'msg': 'Missing required positional only argument',
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
            ArgsKwargs(()),
            Err(
                '3 validation errors for arguments',
                [
                    {
                        'type': 'missing_positional_only_argument',
                        'loc': (0,),
                        'msg': 'Missing required positional only argument',
                        'input': ArgsKwargs(()),
                    },
                    {
                        'type': 'missing_positional_only_argument',
                        'loc': (1,),
                        'msg': 'Missing required positional only argument',
                        'input': ArgsKwargs(()),
                    },
                    {
                        'type': 'missing_positional_only_argument',
                        'loc': (2,),
                        'msg': 'Missing required positional only argument',
                        'input': ArgsKwargs(()),
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
        # debug(exc_info.value.errors(include_url=False))
        if expected.errors is not None:
            assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [ArgsKwargs((), {'a': 1, 'b': 'a', 'c': True}), ((), {'a': 1, 'b': 'a', 'c': True})],
        [{'a': 1, 'b': 'a', 'c': True}, ((), {'a': 1, 'b': 'a', 'c': True})],
        [ArgsKwargs((), {'a': '1', 'b': 'a', 'c': 'True'}), ((), {'a': 1, 'b': 'a', 'c': True})],
        [ArgsKwargs((), {'a': 1, 'b': 'a', 'c': True}), ((), {'a': 1, 'b': 'a', 'c': True})],
        [ArgsKwargs((1,), {'a': 1, 'b': 'a', 'c': True}), Err('type=unexpected_positional_argument,')],
        [
            ArgsKwargs((), {'a': 1, 'b': 'a', 'c': True, 'd': 'wrong'}),
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
            ArgsKwargs((), {'a': 1, 'b': 'a'}),
            Err(
                'type=missing_keyword_only_argument,',
                [
                    {
                        'type': 'missing_keyword_only_argument',
                        'loc': ('c',),
                        'msg': 'Missing required keyword only argument',
                        'input': ArgsKwargs((), {'a': 1, 'b': 'a'}),
                    }
                ],
            ),
        ],
        [
            ArgsKwargs((), {'a': 'x', 'b': 'a', 'c': 'wrong'}),
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
            ArgsKwargs(()),
            Err(
                '',
                [
                    {
                        'type': 'missing_keyword_only_argument',
                        'loc': ('a',),
                        'msg': 'Missing required keyword only argument',
                        'input': ArgsKwargs(()),
                    },
                    {
                        'type': 'missing_keyword_only_argument',
                        'loc': ('b',),
                        'msg': 'Missing required keyword only argument',
                        'input': ArgsKwargs(()),
                    },
                    {
                        'type': 'missing_keyword_only_argument',
                        'loc': ('c',),
                        'msg': 'Missing required keyword only argument',
                        'input': ArgsKwargs(()),
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
        # debug(exc_info.value.errors(include_url=False))
        if expected.errors is not None:
            assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [{'a': 1, 'b': 'bb', 'c': True}, ((), {'a': 1, 'b': 'bb', 'c': True})],
        [ArgsKwargs((), {'a': 1, 'b': 'bb', 'c': True}), ((), {'a': 1, 'b': 'bb', 'c': True})],
        [ArgsKwargs((1, 'bb'), {'c': True}), ((1, 'bb'), {'c': True})],
        [ArgsKwargs((1,), {'b': 'bb', 'c': True}), ((1,), {'b': 'bb', 'c': True})],
        [
            ArgsKwargs((1,), {'a': 11, 'b': 'bb', 'c': True}),
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
            ArgsKwargs((1, 'bb', 'cc'), {'b': 'bb', 'c': True}),
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
            ArgsKwargs((1, 'b1'), {'a': 11, 'b': 'b2', 'c': True}),
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
        # debug(exc_info.value.errors(include_url=False))
        if expected.errors is not None:
            assert exc_info.value.errors(include_url=False) == expected.errors
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
        # debug(exc_info.value.errors(include_url=False))
        if expected.errors is not None:
            assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [{'a': 1}, ((), {'a': 1})],
        [ArgsKwargs((), {'a': 1}), ((), {'a': 1})],
        [ArgsKwargs((), {'a': 1}), ((), {'a': 1})],
        [ArgsKwargs(()), ((), {'a': 1})],
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
        # debug(exc_info.value.errors(include_url=False))
        if expected.errors is not None:
            assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [[1, 2, 3], ((1, 2, 3), {})],
        [ArgsKwargs((1, 2, 3)), ((1, 2, 3), {})],
        [[1], ((1,), {})],
        [[], ((), {})],
        [ArgsKwargs((1, 2, 3), {'a': 1}), Err('a\n  Unexpected keyword argument [type=unexpected_keyword_argument,')],
    ],
    ids=repr,
)
def test_var_args_only(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'arguments', 'arguments_schema': [], 'var_args_schema': {'type': 'int'}})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)
        # debug(exc_info.value.errors(include_url=False))
        if expected.errors is not None:
            assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [[1, 2, 3], ((1, 2, 3), {})],
        [['1', '2', '3'], ((1, 2, 3), {})],
        [[1], ((1,), {})],
        [[], Err('0\n  Missing required positional only argument')],
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
        [ArgsKwargs((1, 2, 3), {'a': 1}), Err('a\n  Unexpected keyword argument [type=unexpected_keyword_argument,')],
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
        # debug(exc_info.value.errors(include_url=False))
        if expected.errors is not None:
            assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [ArgsKwargs((1, 'a', 'true'), {'b': 'bb', 'c': 3}), ((1, 'a', True), {'b': 'bb', 'c': 3})],
        [ArgsKwargs((1, 'a'), {'a': 'true', 'b': 'bb', 'c': 3}), ((1, 'a'), {'a': True, 'b': 'bb', 'c': 3})],
        [
            ArgsKwargs((1, 'a', 'true', 4, 5), {'b': 'bb', 'c': 3}),
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
            assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        [ArgsKwargs(()), ((), {})],
        [[], ((), {})],
        [[1], Err('0\n  Unexpected positional argument [type=unexpected_positional_argument,')],
        [{'a': 1}, Err('a\n  Unexpected keyword argument [type=unexpected_keyword_argument,')],
        [
            ArgsKwargs((1,), {'a': 2}),
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
        # debug(exc_info.value.errors(include_url=False))
        if expected.errors is not None:
            assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        assert v.validate_test(input_value) == expected


def double_or_bust(input_value, info):
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
                    'schema': {'type': 'function-plain', 'function': {'type': 'general', 'function': double_or_bust}},
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
        [ArgsKwargs((1, 2)), ((1, 2), {})],
        [ArgsKwargs((1,)), ((1,), {'b': 42})],
        [ArgsKwargs((1,), {'b': 3}), ((1,), {'b': 3})],
        [ArgsKwargs((), {'a': 1}), ((), {'a': 1, 'b': 42})],
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
        [ArgsKwargs((1, 2)), ((1, 2), {})],
        [ArgsKwargs((1,), {'b': '4', 'c': 'a'}), ((1,), {'b': 4, 'c': 'a'})],
        [ArgsKwargs((1, 2), {'x': 'abc'}), ((1, 2), {'x': 'abc'})],
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
        [ArgsKwargs((1,)), ((1,), {})],
        [ArgsKwargs((), {'Foo': 1}), ((), {'a': 1})],
        [ArgsKwargs((), {'a': 1}), Err('Foo\n  Missing required argument [type=missing_argument,')],
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
        [ArgsKwargs((1,)), ((1,), {})],
        [ArgsKwargs((), {'Foo': 1}), ((), {'a': 1})],
        [ArgsKwargs((), {'a': 1}), ((), {'a': 1})],
        [ArgsKwargs((), {'a': 1, 'b': 2}), Err('b\n  Unexpected keyword argument [type=unexpected_keyword_argument,')],
        [
            ArgsKwargs((), {'a': 1, 'Foo': 2}),
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
        validated_args, validated_kwargs = validator.validate_python(ArgsKwargs(args, kwargs))
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

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': (1,),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'b',
        },
        {
            'type': 'missing_keyword_only_argument',
            'loc': ('c',),
            'msg': 'Missing required keyword only argument',
            'input': ArgsKwargs((1, 'b')),
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        foobar(1, 'b', c='c')

    assert exc_info.value.errors(include_url=False) == [
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
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'missing_positional_only_argument',
            'loc': (1,),
            'msg': 'Missing required positional only argument',
            'input': ArgsKwargs(('1',), {'b': 2, 'c': 3}),
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


def test_error_display(pydantic_version):
    v = SchemaValidator(
        core_schema.arguments_schema(
            [
                core_schema.arguments_parameter('a', core_schema.int_schema()),
                core_schema.arguments_parameter('b', core_schema.int_schema()),
            ]
        )
    )
    assert v.validate_python(ArgsKwargs((1,), {'b': '2'})) == ((1,), {'b': 2})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(ArgsKwargs((), {'a': 1}))

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'missing_argument',
            'loc': ('b',),
            'msg': 'Missing required argument',
            'input': ArgsKwargs((), {'a': 1}),
        }
    ]
    # insert_assert(str(exc_info.value))
    assert str(exc_info.value) == (
        "1 validation error for arguments\n"
        "b\n"
        "  Missing required argument [type=missing_argument, "
        "input_value=ArgsKwargs((), {'a': 1}), input_type=ArgsKwargs]\n"
        f"    For further information visit https://errors.pydantic.dev/{pydantic_version}/v/missing_argument"
    )
    # insert_assert(exc_info.value.json(include_url=False))
    assert exc_info.value.json(include_url=False) == (
        '[{"type":"missing_argument","loc":["b"],"msg":"Missing required argument",'
        '"input":"ArgsKwargs((), {\'a\': 1})"}]'
    )
