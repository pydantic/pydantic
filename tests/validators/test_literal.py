import re
from enum import Enum
from typing import Any, Callable, List

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema

from ..conftest import Err, PyAndJson, plain_repr


@pytest.mark.parametrize(
    'kwarg_expected,input_value,expected',
    [
        ([1], 1, 1),
        pytest.param(
            [1],
            2,
            Err(
                'Input should be 1 [type=literal_error, input_value=2, input_type=int]',
                [
                    {
                        'type': 'literal_error',
                        'loc': (),
                        'msg': 'Input should be 1',
                        'input': 2,
                        'ctx': {'expected': '1'},
                    }
                ],
            ),
            id='wrong-single-int',
        ),
        (['foo'], 'foo', 'foo'),
        pytest.param(
            ['foo'],
            'bar',
            Err(
                "Input should be 'foo' [type=literal_error, input_value='bar', input_type=str]",
                [
                    {
                        'type': 'literal_error',
                        'loc': (),
                        'msg': "Input should be 'foo'",
                        'input': 'bar',
                        'ctx': {'expected': "'foo'"},
                    }
                ],
            ),
            id='wrong-single-str',
        ),
        ([1, 2], 1, 1),
        ([1, 2], 2, 2),
        pytest.param(
            [1, 2],
            3,
            Err('Input should be 1 or 2 [type=literal_error, input_value=3, input_type=int]'),
            id='wrong-multiple-int',
        ),
        ([1, 2, 3, 4], 4, 4),
        pytest.param(
            [1, 2, 3, 4],
            5,
            Err(
                'Input should be 1, 2, 3 or 4 [type=literal_error, input_value=5, input_type=int]',
                [
                    {
                        'type': 'literal_error',
                        'loc': (),
                        'msg': 'Input should be 1, 2, 3 or 4',
                        'input': 5,
                        'ctx': {'expected': '1, 2, 3 or 4'},
                    }
                ],
            ),
            id='wrong-multiple-int',
        ),
        (['a', 'b'], 'a', 'a'),
        pytest.param(
            ['a', 'b'],
            'c',
            Err("Input should be 'a' or 'b' [type=literal_error, input_value=\'c\', input_type=str]"),
            id='wrong-multiple-str',
        ),
        ([1, '1'], 1, 1),
        ([1, '1'], '1', '1'),
        pytest.param(
            [1, '1'],
            '2',
            Err(
                "Input should be 1 or '1' [type=literal_error, input_value='2', input_type=str]",
                [
                    {
                        'type': 'literal_error',
                        'loc': (),
                        'msg': "Input should be 1 or '1'",
                        'input': '2',
                        'ctx': {'expected': "1 or '1'"},
                    }
                ],
            ),
            id='wrong-str-int',
        ),
    ],
)
def test_literal_py_and_json(py_and_json: PyAndJson, kwarg_expected, input_value, expected):
    v = py_and_json({'type': 'literal', 'expected': kwarg_expected})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)
        if expected.errors is not None:
            # debug(exc_info.value.errors(include_url=False))
            assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'kwarg_expected,input_value,expected',
    [
        ([1, b'whatever'], b'whatever', b'whatever'),
        ([(1, 2), (3, 4)], (1, 2), (1, 2)),
        ([(1, 2), (3, 4)], (3, 4), (3, 4)),
        pytest.param(
            [1, b'whatever'],
            3,
            Err("Input should be 1 or b'whatever' [type=literal_error, input_value=3, input_type=int]"),
            id='wrong-general',
        ),
        ([b'bite'], b'bite', b'bite'),
        pytest.param(
            [b'bite'],
            'spoon',
            Err(
                "Input should be b'bite' [type=literal_error, input_value='spoon', input_type=str]",
                [
                    {
                        'type': 'literal_error',
                        'loc': (),
                        'msg': "Input should be 1 or '1'",
                        'input': '2',
                        'ctx': {'expected': "1 or '1'"},
                    }
                ],
            ),
            id='single-byte',
        ),
    ],
)
def test_literal_not_json(kwarg_expected, input_value, expected):
    v = SchemaValidator({'type': 'literal', 'expected': kwarg_expected})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_python(input_value)
            if expected.errors is not None:
                # debug(exc_info.value.errors(include_url=False))
                assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        assert v.validate_python(input_value) == expected


def test_build_error():
    with pytest.raises(SchemaError, match='SchemaError: `expected` should have length > 0'):
        SchemaValidator({'type': 'literal', 'expected': []})


def test_literal_none():
    v = SchemaValidator(core_schema.literal_schema([None]))
    assert v.isinstance_python(None) is True
    assert v.isinstance_python(0) is False
    expected_repr_start = 'SchemaValidator(title="literal[None]"'
    assert plain_repr(v)[: len(expected_repr_start)] == expected_repr_start


def test_union():
    v = SchemaValidator(core_schema.union_schema([core_schema.literal_schema(['a', 'b']), core_schema.int_schema()]))
    assert v.validate_python('a') == 'a'
    assert v.validate_python(4) == 4
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('c')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': ("literal['a','b']",),
            'msg': "Input should be 'a' or 'b'",
            'input': 'c',
            'ctx': {'expected': "'a' or 'b'"},
        },
        {
            'type': 'int_parsing',
            'loc': ('int',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'c',
        },
    ]


def test_enum_value():
    class FooEnum(Enum):
        foo = 'foo_value'
        bar = 'bar_value'

    v = SchemaValidator(core_schema.literal_schema([FooEnum.foo]))
    assert v.validate_python(FooEnum.foo) == FooEnum.foo
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('foo_value')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': (),
            'msg': "Input should be <FooEnum.foo: 'foo_value'>",
            'input': 'foo_value',
            'ctx': {'expected': "<FooEnum.foo: 'foo_value'>"},
        }
    ]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('unknown')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': (),
            'msg': "Input should be <FooEnum.foo: 'foo_value'>",
            'input': 'unknown',
            'ctx': {'expected': "<FooEnum.foo: 'foo_value'>"},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('"foo_value"')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': (),
            'msg': "Input should be <FooEnum.foo: 'foo_value'>",
            'input': 'foo_value',
            'ctx': {'expected': "<FooEnum.foo: 'foo_value'>"},
        }
    ]


def test_str_enum_values():
    class Foo(str, Enum):
        foo = 'foo_value'
        bar = 'bar_value'

    v = SchemaValidator(core_schema.literal_schema([Foo.foo]))

    assert v.validate_python(Foo.foo) == Foo.foo
    assert v.validate_python('foo_value') == Foo.foo
    assert v.validate_json('"foo_value"') == Foo.foo

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('unknown')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': (),
            'msg': "Input should be <Foo.foo: 'foo_value'>",
            'input': 'unknown',
            'ctx': {'expected': "<Foo.foo: 'foo_value'>"},
        }
    ]


def test_int_enum_values():
    class Foo(int, Enum):
        foo = 2
        bar = 3

    v = SchemaValidator(core_schema.literal_schema([Foo.foo]))

    assert v.validate_python(Foo.foo) == Foo.foo
    assert v.validate_python(2) == Foo.foo
    assert v.validate_json('2') == Foo.foo

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(4)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': (),
            'msg': 'Input should be <Foo.foo: 2>',
            'input': 4,
            'ctx': {'expected': '<Foo.foo: 2>'},
        }
    ]


@pytest.mark.parametrize(
    'reverse, err',
    [
        (
            lambda x: list(reversed(x)),
            [
                {
                    'type': 'literal_error',
                    'loc': (),
                    'msg': 'Input should be <Foo.foo: 1> or 1',
                    'input': 2,
                    'ctx': {'expected': '<Foo.foo: 1> or 1'},
                }
            ],
        ),
        (
            lambda x: x,
            [
                {
                    'type': 'literal_error',
                    'loc': (),
                    'msg': 'Input should be 1 or <Foo.foo: 1>',
                    'input': 2,
                    'ctx': {'expected': '1 or <Foo.foo: 1>'},
                }
            ],
        ),
    ],
)
def test_mix_int_enum_with_int(reverse: Callable[[List[Any]], List[Any]], err: Any):
    class Foo(int, Enum):
        foo = 1

    v = SchemaValidator(core_schema.literal_schema(reverse([1, Foo.foo])))

    assert v.validate_python(Foo.foo) is Foo.foo
    val = v.validate_python(1)
    assert val == 1 and val is not Foo.foo
    val = v.validate_json('1')
    assert val == 1 and val is not Foo.foo

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(2)
    assert exc_info.value.errors(include_url=False) == err


@pytest.mark.parametrize(
    'reverse, err',
    [
        (
            lambda x: list(reversed(x)),
            [
                {
                    'type': 'literal_error',
                    'loc': (),
                    'msg': "Input should be <Foo.foo: 'foo_val'> or 'foo_val'",
                    'input': 'bar_val',
                    'ctx': {'expected': "<Foo.foo: 'foo_val'> or 'foo_val'"},
                }
            ],
        ),
        (
            lambda x: x,
            [
                {
                    'type': 'literal_error',
                    'loc': (),
                    'msg': "Input should be 'foo_val' or <Foo.foo: 'foo_val'>",
                    'input': 'bar_val',
                    'ctx': {'expected': "'foo_val' or <Foo.foo: 'foo_val'>"},
                }
            ],
        ),
    ],
)
def test_mix_str_enum_with_str(reverse: Callable[[List[Any]], List[Any]], err: Any):
    class Foo(str, Enum):
        foo = 'foo_val'

    v = SchemaValidator(core_schema.literal_schema(reverse(['foo_val', Foo.foo])))

    assert v.validate_python(Foo.foo) is Foo.foo
    val = v.validate_python('foo_val')
    assert val == 'foo_val' and val is not Foo.foo
    val = v.validate_json('"foo_val"')
    assert val == 'foo_val' and val is not Foo.foo

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('bar_val')
    assert exc_info.value.errors(include_url=False) == err
