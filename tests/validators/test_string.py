import re
from decimal import Decimal
from typing import Any, Dict, Union

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema

from ..conftest import Err, PyAndJson, plain_repr


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('foobar', 'foobar'),
        (123, Err('Input should be a valid string [type=string_type, input_value=123, input_type=int]')),
        (123.456, Err('Input should be a valid string [type=string_type, input_value=123.456, input_type=float]')),
        (False, Err('Input should be a valid string [type=string_type')),
        (True, Err('Input should be a valid string [type=string_type')),
        ([], Err('Input should be a valid string [type=string_type, input_value=[], input_type=list]')),
    ],
)
def test_str(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'str'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('foobar', 'foobar'),
        ('🐈 Hello \ud800World', '🐈 Hello \ud800World'),
        (b'foobar', 'foobar'),
        (bytearray(b'foobar'), 'foobar'),
        (
            b'\x81',
            Err('Input should be a valid string, unable to parse raw data as a unicode string [type=string_unicode'),
        ),
        (
            bytearray(b'\x81'),
            Err('Input should be a valid string, unable to parse raw data as a unicode string [type=string_unicode'),
        ),
        # null bytes are very annoying, but we can't really block them here
        (b'\x00', '\x00'),
        (123, Err('Input should be a valid string [type=string_type, input_value=123, input_type=int]')),
        (
            Decimal('123'),
            Err("Input should be a valid string [type=string_type, input_value=Decimal('123'), input_type=Decimal]"),
        ),
    ],
)
def test_str_not_json(input_value, expected):
    v = SchemaValidator({'type': 'str'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({}, 'abc', 'abc'),
        ({'strict': True}, 'Foobar', 'Foobar'),
        ({'to_upper': True}, 'fooBar', 'FOOBAR'),
        ({'to_lower': True}, 'fooBar', 'foobar'),
        ({'strip_whitespace': True}, ' foobar  ', 'foobar'),
        ({'strip_whitespace': True, 'to_upper': True}, ' fooBar', 'FOOBAR'),
        ({'min_length': 5}, '12345', '12345'),
        ({'min_length': 5}, '1234', Err('String should have at least 5 characters [type=string_too_short')),
        ({'max_length': 5}, '12345', '12345'),
        ({'max_length': 5}, '123456', Err('String should have at most 5 characters [type=string_too_long')),
        ({'pattern': r'^\d+$'}, '12345', '12345'),
        ({'pattern': r'\d+$'}, 'foobar 123', 'foobar 123'),
        ({'pattern': r'^\d+$'}, '12345a', Err("String should match pattern '^\\d+$' [type=string_pattern_mismatch")),
        # strip comes after length check
        ({'max_length': 5, 'strip_whitespace': True}, '1234  ', '1234'),
        # to_upper and strip comes after pattern check
        ({'to_upper': True, 'pattern': 'abc'}, 'abc', 'ABC'),
        ({'strip_whitespace': True, 'pattern': r'\d+$'}, 'foobar 123 ', 'foobar 123'),
        ({'min_length': 1}, '🐈 Hello', '🐈 Hello'),
    ],
)
def test_constrained_str(py_and_json: PyAndJson, kwargs: Dict[str, Any], input_value, expected):
    v = py_and_json({'type': 'str', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({}, b'abc', 'abc'),
        ({'strict': True}, 'Foobar', 'Foobar'),
        (
            {'strict': True},
            123,
            Err('Input should be a valid string [type=string_type, input_value=123, input_type=int]'),
        ),
    ],
)
def test_constrained_str_py_only(kwargs: Dict[str, Any], input_value, expected):
    v = SchemaValidator({'type': 'str', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


def test_unicode_error():
    # `.to_str()` Returns a `UnicodeEncodeError` if the input is not valid unicode (containing unpaired surrogates).
    # https://github.com/PyO3/pyo3/blob/6503128442b8f3e767c663a6a8d96376d7fb603d/src/types/string.rs#L477
    v = SchemaValidator({'type': 'str', 'min_length': 1})
    assert v.validate_python('🐈 Hello') == '🐈 Hello'

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('🐈 Hello \ud800World')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_unicode',
            'loc': (),
            'msg': 'Input should be a valid string, unable to parse raw data as a unicode string',
            'input': '🐈 Hello \ud800World',
        }
    ]


@pytest.mark.parametrize(
    ('data', 'max_length', 'error'),
    [
        pytest.param('test', 5, None, id='short string'),
        pytest.param('test long', 5, 'String should have at most 5 characters', id='long string'),
        pytest.param('␛⯋℃▤', 5, None, id='short string with unicode characters'),
        pytest.param(
            '␛⯋℃▤⩥⠫⳼⣪⨺✒⧐♳⩚⏭⏣⍥┙⧃Ⰴ┽⏏♜',
            5,
            'String should have at most 5 characters',
            id='long string with unicode characters',
        ),
        pytest.param('а' * 25, 32, None, id='a lot of `а`s'),
    ],
)
def test_str_constrained(data: str, max_length: int, error: Union[re.Pattern, None]):
    v = SchemaValidator({'type': 'str', 'max_length': max_length})
    if error is None:
        assert v.validate_python(data) == data
    else:
        with pytest.raises(ValidationError, match=error):
            v.validate_python(data)


def test_str_constrained_config():
    v = SchemaValidator({'type': 'str'}, {'str_max_length': 5})
    assert v.validate_python('test') == 'test'

    with pytest.raises(ValidationError, match='String should have at most 5 characters'):
        v.validate_python('test long')


def test_invalid_regex():
    # TODO uncomment and fix once #150 is done
    # with pytest.raises(SchemaError) as exc_info:
    #     SchemaValidator({'type': 'str', 'pattern': 123})
    # assert exc_info.value.args[0] == (
    #     'Error building "str" validator:\n  TypeError: \'int\' object cannot be converted to \'PyString\''
    # )
    with pytest.raises(SchemaError) as exc_info:
        SchemaValidator({'type': 'str', 'pattern': '(abc'})
    assert exc_info.value.args[0] == (
        'Error building "str" validator:\n'
        '  SchemaError: regex parse error:\n'
        '    (abc\n'
        '    ^\n'
        'error: unclosed group'
    )


def test_regex_error():
    v = SchemaValidator({'type': 'str', 'pattern': '11'})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('12')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_pattern_mismatch',
            'loc': (),
            'msg': "String should match pattern '11'",
            'input': '12',
            'ctx': {'pattern': '11'},
        }
    ]


def test_default_validator():
    v = SchemaValidator(core_schema.str_schema(strict=True, to_lower=False), {'str_strip_whitespace': False})
    assert plain_repr(v) == 'SchemaValidator(title="str",validator=Str(StrValidator{strict:true}),definitions=[])'


@pytest.fixture(scope='session', name='FruitEnum')
def fruit_enum_fixture():
    from enum import Enum

    class FruitEnum(str, Enum):
        pear = 'pear'
        banana = 'banana'

    return FruitEnum


@pytest.mark.parametrize('to_lower', [False, True], ids=repr)
def test_strict_subclass(to_lower: bool):
    v = SchemaValidator(core_schema.str_schema(strict=True, to_lower=to_lower))

    class StrSubclass(str):
        pass

    res = v.validate_python(StrSubclass('ABC'))
    assert res == 'abc' if to_lower else 'ABC'


@pytest.mark.parametrize('kwargs', [{}, {'to_lower': True}], ids=repr)
def test_lax_subclass(FruitEnum, kwargs):
    v = SchemaValidator(core_schema.str_schema(**kwargs))
    assert v.validate_python('foobar') == 'foobar'
    assert v.validate_python(b'foobar') == 'foobar'
    p = v.validate_python(FruitEnum.pear)
    assert p == 'pear'
    assert type(p) is str
    assert repr(p) == "'pear'"


def test_subclass_preserved() -> None:
    class StrSubclass(str):
        pass

    v = SchemaValidator(core_schema.str_schema())

    assert not isinstance(v.validate_python(StrSubclass('')), StrSubclass)
    assert not isinstance(v.validate_python(StrSubclass(''), strict=True), StrSubclass)

    # unions do a first pass in strict mode
    # so verify that they don't match the str schema in strict mode
    # and preserve the type
    v = SchemaValidator(core_schema.union_schema([core_schema.str_schema(), core_schema.int_schema()]))

    assert not isinstance(v.validate_python(StrSubclass('')), StrSubclass)
    assert not isinstance(v.validate_python(StrSubclass(''), strict=True), StrSubclass)
