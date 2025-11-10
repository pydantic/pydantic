import enum
import os
import pickle
import re
import subprocess
import sys
from decimal import Decimal
from typing import Any, Optional
from unittest.mock import patch

import pytest
from dirty_equals import HasRepr, IsInstance, IsJson, IsStr
from pydantic_core import (
    CoreConfig,
    PydanticCustomError,
    PydanticKnownError,
    PydanticOmit,
    SchemaValidator,
    ValidationError,
    core_schema,
)
from pydantic_core._pydantic_core import list_all_errors

from .conftest import PyAndJson


def test_pydantic_value_error():
    e = PydanticCustomError(
        'my_error', 'this is a custom error {missed} {foo} {bar} {spam}', {'foo': 'X', 'bar': 42, 'spam': []}
    )
    assert e.message() == 'this is a custom error {missed} X 42 []'
    assert e.message_template == 'this is a custom error {missed} {foo} {bar} {spam}'
    assert e.type == 'my_error'
    assert e.context == {'foo': 'X', 'bar': 42, 'spam': []}
    assert str(e) == 'this is a custom error {missed} X 42 []'
    assert repr(e) == (
        "this is a custom error {missed} X 42 [] [type=my_error, context={'foo': 'X', 'bar': 42, 'spam': []}]"
    )


@pytest.mark.parametrize(
    'msg,result_msg', [('my custom error', 'my custom error'), ('my custom error {foo}', "my custom error {'bar': []}")]
)
def test_pydantic_value_error_nested_ctx(msg: str, result_msg: str):
    ctx = {'foo': {'bar': []}}
    e = PydanticCustomError('my_error', msg, ctx)
    assert e.message() == result_msg
    assert e.message_template == msg
    assert e.type == 'my_error'
    assert e.context == ctx
    assert str(e) == result_msg
    assert repr(e) == f'{result_msg} [type=my_error, context={ctx}]'


def test_pydantic_value_error_none():
    e = PydanticCustomError('my_error', 'this is a custom error {missed}')
    assert e.message() == 'this is a custom error {missed}'
    assert e.message_template == 'this is a custom error {missed}'
    assert e.type == 'my_error'
    assert e.context is None
    assert str(e) == 'this is a custom error {missed}'
    assert repr(e) == 'this is a custom error {missed} [type=my_error, context=None]'


def test_pydantic_value_error_usage():
    def f(input_value, info):
        raise PydanticCustomError('my_error', 'this is a custom error {foo} {bar}', {'foo': 'FOOBAR', 'bar': 42})

    v = SchemaValidator(core_schema.with_info_plain_validator_function(f))

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(42)

    assert exc_info.value.errors() == [
        {
            'type': 'my_error',
            'loc': (),
            'msg': 'this is a custom error FOOBAR 42',
            'input': 42,
            'ctx': {'foo': 'FOOBAR', 'bar': 42},
        }
    ]


def test_pydantic_value_error_invalid_dict():
    def my_function(input_value, info):
        raise PydanticCustomError('my_error', 'this is a custom error {foo}', {(): 'foobar'})

    v = SchemaValidator(core_schema.with_info_plain_validator_function(my_function))

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(42)

    assert str(exc_info.value) == (
        '1 validation error for function-plain[my_function()]\n'
        "  (error rendering message: TypeError: 'tuple' object cannot be converted to 'PyString') "
        '[type=my_error, input_value=42, input_type=int]'
    )
    with pytest.raises(TypeError, match="'tuple' object cannot be converted to 'PyString'"):
        exc_info.value.errors(include_url=False)


def test_pydantic_value_error_invalid_type():
    def f(input_value, info):
        raise PydanticCustomError('my_error', 'this is a custom error {foo}', [('foo', 123)])

    v = SchemaValidator(core_schema.with_info_plain_validator_function(f))

    with pytest.raises(TypeError, match="argument 'context': 'list' object cannot be converted to 'PyDict'"):
        v.validate_python(42)


def test_validator_instance_plain():
    class CustomValidator:
        def __init__(self):
            self.foo = 42
            self.bar = 'before'

        def validate(self, input_value, info):
            return f'{input_value} {self.foo} {self.bar}'

    c = CustomValidator()
    v = SchemaValidator(core_schema.with_info_plain_validator_function(c.validate, metadata={'instance': c}))
    c.foo += 1

    assert v.validate_python('input value') == 'input value 43 before'
    c.bar = 'changed'
    assert v.validate_python('input value') == 'input value 43 changed'


def test_validator_instance_after():
    class CustomValidator:
        def __init__(self):
            self.foo = 42

        def validate(self, input_value, info):
            assert isinstance(input_value, str)
            return f'{input_value} {self.foo}'

    c = CustomValidator()
    v = SchemaValidator(
        core_schema.with_info_after_validator_function(c.validate, core_schema.str_schema(), metadata={'instance': c})
    )
    c.foo += 1

    assert v.validate_python('input value') == 'input value 43'
    assert v.validate_python(b'is bytes') == 'is bytes 43'


def test_pydantic_error_type():
    e = PydanticKnownError('json_invalid', {'error': 'Test'})
    assert e.message() == 'Invalid JSON: Test'
    assert e.type == 'json_invalid'
    assert e.context == {'error': 'Test'}
    assert str(e) == 'Invalid JSON: Test'
    assert repr(e) == "Invalid JSON: Test [type=json_invalid, context={'error': 'Test'}]"


def test_pydantic_error_type_nested_ctx():
    ctx = {'error': 'Test', 'foo': {'bar': []}}
    e = PydanticKnownError('json_invalid', ctx)
    assert e.message() == 'Invalid JSON: Test'
    assert e.type == 'json_invalid'
    assert e.context == ctx
    assert str(e) == 'Invalid JSON: Test'
    assert repr(e) == f'Invalid JSON: Test [type=json_invalid, context={ctx}]'


def test_pydantic_error_type_raise_no_ctx():
    def f(input_value, info):
        raise PydanticKnownError('finite_number')

    v = SchemaValidator(core_schema.with_info_before_validator_function(f, core_schema.int_schema()))

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(4)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'finite_number', 'loc': (), 'msg': 'Input should be a finite number', 'input': 4}
    ]


@pytest.mark.parametrize(
    'extra', [{}, {'foo': 1}, {'foo': {'bar': []}}, {'foo': {'bar': object()}}, {'foo': Decimal('42.1')}]
)
def test_pydantic_error_type_raise_ctx(extra: dict):
    ctx = {'gt': 42, **extra}

    def f(input_value, info):
        raise PydanticKnownError('greater_than', ctx)

    v = SchemaValidator(core_schema.with_info_before_validator_function(f, core_schema.int_schema()))

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(4)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'greater_than', 'loc': (), 'msg': 'Input should be greater than 42', 'input': 4, 'ctx': ctx}
    ]


@pytest.mark.parametrize('ctx', [None, {}])
def test_pydantic_error_type_raise_custom_no_ctx(ctx: Optional[dict]):
    def f(input_value, info):
        raise PydanticKnownError('int_type', ctx)

    v = SchemaValidator(core_schema.with_info_before_validator_function(f, core_schema.int_schema()))

    expect_ctx = {'ctx': {}} if ctx is not None else {}

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(4)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': (), 'msg': 'Input should be a valid integer', 'input': 4, **expect_ctx}
    ]


@pytest.mark.parametrize(
    'extra', [{}, {'foo': 1}, {'foo': {'bar': []}}, {'foo': {'bar': object()}}, {'foo': Decimal('42.1')}]
)
def test_pydantic_custom_error_type_raise_custom_ctx(extra: dict):
    ctx = {'val': 42, **extra}

    def f(input_value, info):
        raise PydanticCustomError('my_error', 'my message with {val}', ctx)

    v = SchemaValidator(core_schema.with_info_before_validator_function(f, core_schema.int_schema()))

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(4)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'my_error', 'loc': (), 'msg': 'my message with 42', 'input': 4, 'ctx': ctx}
    ]


@pytest.mark.parametrize('ctx', [None, {}])
def test_pydantic_custom_error_type_raise_custom_no_ctx(ctx: Optional[dict]):
    def f(input_value, info):
        raise PydanticCustomError('my_error', 'my message', ctx)

    v = SchemaValidator(core_schema.with_info_before_validator_function(f, core_schema.int_schema()))

    expect_ctx = {'ctx': {}} if ctx is not None else {}

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(4)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'my_error', 'loc': (), 'msg': 'my message', 'input': 4, **expect_ctx}
    ]


all_errors = [
    ('no_such_attribute', "Object has no attribute 'wrong_name'", {'attribute': 'wrong_name'}),
    ('json_invalid', 'Invalid JSON: foobar', {'error': 'foobar'}),
    ('json_type', 'JSON input should be string, bytes or bytearray', None),
    (
        'needs_python_object',
        'Cannot check `isinstance` when validating from json, use a JsonOrPython validator instead',
        {'method_name': 'isinstance'},
    ),
    ('recursion_loop', 'Recursion error - cyclic reference detected', None),
    ('model_type', 'Input should be a valid dictionary or instance of Foobar', {'class_name': 'Foobar'}),
    ('model_attributes_type', 'Input should be a valid dictionary or object to extract fields from', None),
    ('dataclass_exact_type', 'Input should be an instance of Foobar', {'class_name': 'Foobar'}),
    ('dataclass_type', 'Input should be a dictionary or an instance of Foobar', {'class_name': 'Foobar'}),
    (
        'default_factory_not_called',
        'The default factory uses validated data, but at least one validation error occurred',
        None,
    ),
    ('missing', 'Field required', None),
    ('frozen_field', 'Field is frozen', None),
    ('frozen_instance', 'Instance is frozen', None),
    ('extra_forbidden', 'Extra inputs are not permitted', None),
    ('invalid_key', 'Keys should be strings', None),
    ('get_attribute_error', 'Error extracting attribute: foo', {'error': 'foo'}),
    ('none_required', 'Input should be None', None),
    ('enum', 'Input should be foo', {'expected': 'foo'}),
    ('greater_than', 'Input should be greater than 42.1', {'gt': 42.1}),
    ('greater_than', 'Input should be greater than 42.1', {'gt': '42.1'}),
    ('greater_than', 'Input should be greater than 2020-01-01', {'gt': '2020-01-01'}),
    ('greater_than_equal', 'Input should be greater than or equal to 42.1', {'ge': 42.1}),
    ('less_than', 'Input should be less than 42.1', {'lt': 42.1}),
    ('less_than_equal', 'Input should be less than or equal to 42.1', {'le': 42.1}),
    ('finite_number', 'Input should be a finite number', None),
    (
        'too_short',
        'Foobar should have at least 42 items after validation, not 40',
        {'field_type': 'Foobar', 'min_length': 42, 'actual_length': 40},
    ),
    (
        'too_long',
        'Foobar should have at most 42 items after validation, not 50',
        {'field_type': 'Foobar', 'max_length': 42, 'actual_length': 50},
    ),
    ('string_type', 'Input should be a valid string', None),
    ('string_sub_type', 'Input should be a string, not an instance of a subclass of str', None),
    ('string_unicode', 'Input should be a valid string, unable to parse raw data as a unicode string', None),
    ('string_pattern_mismatch', "String should match pattern 'foo'", {'pattern': 'foo'}),
    ('string_too_short', 'String should have at least 42 characters', {'min_length': 42}),
    ('string_too_short', 'String should have at least 1 character', {'min_length': 1}),
    ('string_too_long', 'String should have at most 42 characters', {'max_length': 42}),
    ('string_too_long', 'String should have at most 1 character', {'max_length': 1}),
    ('dict_type', 'Input should be a valid dictionary', None),
    ('mapping_type', 'Input should be a valid mapping, error: foobar', {'error': 'foobar'}),
    ('iterable_type', 'Input should be iterable', None),
    ('iteration_error', 'Error iterating over object, error: foobar', {'error': 'foobar'}),
    ('list_type', 'Input should be a valid list', None),
    ('tuple_type', 'Input should be a valid tuple', None),
    ('set_item_not_hashable', 'Set items should be hashable', None),
    ('set_type', 'Input should be a valid set', None),
    ('bool_type', 'Input should be a valid boolean', None),
    ('bool_parsing', 'Input should be a valid boolean, unable to interpret input', None),
    ('int_type', 'Input should be a valid integer', None),
    ('int_parsing', 'Input should be a valid integer, unable to parse string as an integer', None),
    ('int_parsing_size', 'Unable to parse input string as an integer, exceeded maximum size', None),
    ('int_from_float', 'Input should be a valid integer, got a number with a fractional part', None),
    ('multiple_of', 'Input should be a multiple of 42.1', {'multiple_of': 42.1}),
    ('greater_than', 'Input should be greater than 42.1', {'gt': 42.1}),
    ('greater_than_equal', 'Input should be greater than or equal to 42.1', {'ge': 42.1}),
    ('less_than', 'Input should be less than 42.1', {'lt': 42.1}),
    ('less_than_equal', 'Input should be less than or equal to 42.1', {'le': 42.1}),
    ('float_type', 'Input should be a valid number', None),
    ('float_parsing', 'Input should be a valid number, unable to parse string as a number', None),
    ('bytes_type', 'Input should be a valid bytes', None),
    ('bytes_too_short', 'Data should have at least 42 bytes', {'min_length': 42}),
    ('bytes_too_short', 'Data should have at least 1 byte', {'min_length': 1}),
    ('bytes_too_long', 'Data should have at most 42 bytes', {'max_length': 42}),
    ('bytes_too_long', 'Data should have at most 1 byte', {'max_length': 1}),
    (
        'bytes_invalid_encoding',
        'Data should be valid base64: Invalid byte 1, offset 1',
        {'encoding': 'base64', 'encoding_error': 'Invalid byte 1, offset 1'},
    ),
    (
        'bytes_invalid_encoding',
        'Data should be valid hex: Odd number of digits',
        {'encoding': 'hex', 'encoding_error': 'Odd number of digits'},
    ),
    ('value_error', 'Value error, foobar', {'error': ValueError('foobar')}),
    ('assertion_error', 'Assertion failed, foobar', {'error': AssertionError('foobar')}),
    ('literal_error', 'Input should be foo', {'expected': 'foo'}),
    ('literal_error', 'Input should be foo or bar', {'expected': 'foo or bar'}),
    ('missing_sentinel_error', "Input should be the 'MISSING' sentinel", None),
    ('date_type', 'Input should be a valid date', None),
    ('date_parsing', 'Input should be a valid date in the format YYYY-MM-DD, foobar', {'error': 'foobar'}),
    ('date_from_datetime_parsing', 'Input should be a valid date or datetime, foobar', {'error': 'foobar'}),
    ('date_from_datetime_inexact', 'Datetimes provided to dates should have zero time - e.g. be exact dates', None),
    ('date_past', 'Date should be in the past', None),
    ('date_future', 'Date should be in the future', None),
    ('time_type', 'Input should be a valid time', None),
    ('time_parsing', 'Input should be in a valid time format, foobar', {'error': 'foobar'}),
    ('datetime_type', 'Input should be a valid datetime', None),
    ('datetime_parsing', 'Input should be a valid datetime, foobar', {'error': 'foobar'}),
    ('datetime_from_date_parsing', 'Input should be a valid datetime or date, foobar', {'error': 'foobar'}),
    ('datetime_object_invalid', 'Invalid datetime object, got foobar', {'error': 'foobar'}),
    ('datetime_past', 'Input should be in the past', None),
    ('datetime_future', 'Input should be in the future', None),
    ('timezone_naive', 'Input should not have timezone info', None),
    ('timezone_aware', 'Input should have timezone info', None),
    ('timezone_offset', 'Timezone offset of 0 required, got 60', {'tz_expected': 0, 'tz_actual': 60}),
    ('time_delta_type', 'Input should be a valid timedelta', None),
    ('time_delta_parsing', 'Input should be a valid timedelta, foobar', {'error': 'foobar'}),
    ('frozen_set_type', 'Input should be a valid frozenset', None),
    ('is_instance_of', 'Input should be an instance of Foo', {'class': 'Foo'}),
    ('is_subclass_of', 'Input should be a subclass of Foo', {'class': 'Foo'}),
    ('callable_type', 'Input should be callable', None),
    (
        'union_tag_invalid',
        "Input tag 'foo' found using bar does not match any of the expected tags: baz",
        {'discriminator': 'bar', 'tag': 'foo', 'expected_tags': 'baz'},
    ),
    ('union_tag_not_found', 'Unable to extract tag using discriminator foo', {'discriminator': 'foo'}),
    ('arguments_type', 'Arguments must be a tuple, list or a dictionary', None),
    ('missing_argument', 'Missing required argument', None),
    ('unexpected_keyword_argument', 'Unexpected keyword argument', None),
    ('missing_keyword_only_argument', 'Missing required keyword only argument', None),
    ('unexpected_positional_argument', 'Unexpected positional argument', None),
    ('missing_positional_only_argument', 'Missing required positional only argument', None),
    ('multiple_argument_values', 'Got multiple values for argument', None),
    ('url_type', 'URL input should be a string or URL', None),
    ('url_parsing', 'Input should be a valid URL, Foobar', {'error': 'Foobar'}),
    ('url_syntax_violation', 'Input violated strict URL syntax rules, Foobar', {'error': 'Foobar'}),
    ('url_too_long', 'URL should have at most 42 characters', {'max_length': 42}),
    ('url_too_long', 'URL should have at most 1 character', {'max_length': 1}),
    ('url_scheme', 'URL scheme should be "foo", "bar" or "spam"', {'expected_schemes': '"foo", "bar" or "spam"'}),
    ('uuid_type', 'UUID input should be a string, bytes or UUID object', None),
    ('uuid_parsing', 'Input should be a valid UUID, Foobar', {'error': 'Foobar'}),
    ('uuid_version', 'UUID version 42 expected', {'expected_version': 42}),
    ('decimal_type', 'Decimal input should be an integer, float, string or Decimal object', None),
    ('decimal_parsing', 'Input should be a valid decimal', None),
    ('decimal_max_digits', 'Decimal input should have no more than 42 digits in total', {'max_digits': 42}),
    ('decimal_max_digits', 'Decimal input should have no more than 1 digit in total', {'max_digits': 1}),
    ('decimal_max_places', 'Decimal input should have no more than 42 decimal places', {'decimal_places': 42}),
    ('decimal_max_places', 'Decimal input should have no more than 1 decimal place', {'decimal_places': 1}),
    (
        'decimal_whole_digits',
        'Decimal input should have no more than 42 digits before the decimal point',
        {'whole_digits': 42},
    ),
    (
        'decimal_whole_digits',
        'Decimal input should have no more than 1 digit before the decimal point',
        {'whole_digits': 1},
    ),
    (
        'complex_type',
        'Input should be a valid python complex object, a number, or a valid complex string following the rules at https://docs.python.org/3/library/functions.html#complex',
        None,
    ),
    (
        'complex_str_parsing',
        'Input should be a valid complex string following the rules at https://docs.python.org/3/library/functions.html#complex',
        None,
    ),
]


@pytest.mark.parametrize('error_type, message, context', all_errors)
def test_error_type(error_type, message, context):
    e = PydanticKnownError(error_type, context)
    assert e.message() == message
    assert e.type == error_type
    assert e.context == context


def test_all_errors_covered():
    listed_types = {error_type for error_type, *_ in all_errors}
    actual_types = {e['type'] for e in list_all_errors()}
    assert actual_types == listed_types


def test_error_decimal():
    e = PydanticKnownError('greater_than', {'gt': Decimal('42.1')})
    assert e.message() == 'Input should be greater than 42.1'
    assert e.type == 'greater_than'
    assert e.context == {'gt': Decimal('42.1')}


def test_custom_error_decimal():
    e = PydanticCustomError('my_error', 'this is a custom error {foobar}', {'foobar': Decimal('42.010')})
    assert e.message() == 'this is a custom error 42.010'
    assert e.message_template == 'this is a custom error {foobar}'
    assert e.type == 'my_error'
    assert e.context == {'foobar': Decimal('42.010')}


def test_pydantic_value_error_plain(py_and_json: PyAndJson):
    def f(input_value, info):
        raise PydanticCustomError

    v = py_and_json(core_schema.with_info_plain_validator_function(f))
    with pytest.raises(TypeError, match='missing 2 required positional arguments'):
        v.validate_test('4')


@pytest.mark.parametrize('exception', [PydanticOmit(), PydanticOmit])
def test_list_omit_exception(py_and_json: PyAndJson, exception):
    def f(input_value):
        if input_value % 2 == 0:
            raise exception
        return input_value

    v = py_and_json(core_schema.list_schema(core_schema.no_info_after_validator_function(f, core_schema.int_schema())))
    assert v.validate_test([1, 2, '3', '4']) == [1, 3]


def test_omit_exc_repr():
    assert repr(PydanticOmit()) == 'PydanticOmit()'
    assert str(PydanticOmit()) == 'PydanticOmit()'


@pytest.mark.parametrize(
    'error,ctx,expect',
    [
        ('greater_than', {'gt': []}, "GreaterThan: 'gt' context value must be a Number"),
        ('model_type', {'class_name': []}, "ModelType: 'class_name' context value must be a String"),
        ('date_parsing', {'error': []}, "DateParsing: 'error' context value must be a String"),
        ('string_too_short', {'min_length': []}, "StringTooShort: 'min_length' context value must be a usize"),
    ],
)
def test_type_error_error(error: str, ctx: dict, expect: str):
    with pytest.raises(TypeError, match=f'^{expect}$'):
        PydanticKnownError(error, ctx)


def test_custom_context_for_simple_error():
    err = PydanticKnownError('json_type', {'foo': 'bar'})
    assert err.context == {'foo': 'bar'}


def test_all_errors():
    errors = list_all_errors()
    # print(f'{len(errors)=}')
    assert len(errors) == len({e['type'] for e in errors}), 'error types are not unique'
    # insert_assert(errors[:4])
    assert errors[:4] == [
        {
            'type': 'no_such_attribute',
            'message_template_python': "Object has no attribute '{attribute}'",
            'example_message_python': "Object has no attribute ''",
            'example_context': {'attribute': ''},
        },
        {
            'type': 'json_invalid',
            'message_template_python': 'Invalid JSON: {error}',
            'example_message_python': 'Invalid JSON: ',
            'example_context': {'error': ''},
        },
        {
            'type': 'json_type',
            'message_template_python': 'JSON input should be string, bytes or bytearray',
            'example_message_python': 'JSON input should be string, bytes or bytearray',
            'example_context': None,
        },
        {
            'type': 'needs_python_object',
            'message_template_python': 'Cannot check `{method_name}` when validating from json, use a JsonOrPython validator instead',
            'example_message_python': 'Cannot check `` when validating from json, use a JsonOrPython validator instead',
            'example_context': {'method_name': ''},
        },
    ]

    none_required = next(e for e in errors if e['type'] == 'none_required')
    # insert_assert(none_required)
    assert none_required == {
        'type': 'none_required',
        'message_template_python': 'Input should be None',
        'example_message_python': 'Input should be None',
        'message_template_json': 'Input should be null',
        'example_message_json': 'Input should be null',
        'example_context': None,
    }

    error_types = [e['type'] for e in errors]
    if error_types != list(core_schema.ErrorType.__args__):
        literal = ''.join(f'\n    {e!r},' for e in error_types)
        print(f'python code (end of python/pydantic_core/core_schema.py):\n\nErrorType = Literal[{literal}\n]')
        pytest.fail('core_schema.ErrorType needs to be updated')


@pytest.mark.skipif(sys.version_info < (3, 11), reason='This is the modern version used post 3.10.')
def test_validation_error_cause_contents():
    enabled_config: CoreConfig = CoreConfig(validation_error_cause=True)

    def multi_raise_py_error(v: Any) -> Any:
        try:
            raise AssertionError('Wrong')
        except AssertionError as e:
            raise ValueError('Oh no!') from e

    s2 = SchemaValidator(core_schema.no_info_plain_validator_function(multi_raise_py_error), config=enabled_config)
    with pytest.raises(ValidationError) as exc_info:
        s2.validate_python('anything')

    cause_group = exc_info.value.__cause__
    assert isinstance(cause_group, BaseExceptionGroup)  # noqa: F821,RUF100  # gated on 3.11+ above
    assert len(cause_group.exceptions) == 1

    cause = cause_group.exceptions[0]
    assert cause.__notes__
    assert cause.__notes__[-1].startswith('\nPydantic: ')
    assert repr(cause) == repr(ValueError('Oh no!'))
    assert cause.__traceback__ is not None

    sub_cause = cause.__cause__
    assert repr(sub_cause) == repr(AssertionError('Wrong'))
    assert sub_cause.__cause__ is None
    assert sub_cause.__traceback__ is not None

    # Edge case: make sure a deep inner ValidationError(s) causing a validator failure doesn't cause any problems:
    def outer_raise_py_error(v: Any) -> Any:
        try:
            s2.validate_python('anything')
        except ValidationError as e:
            raise ValueError('Sub val failure') from e

    s3 = SchemaValidator(core_schema.no_info_plain_validator_function(outer_raise_py_error), config=enabled_config)
    with pytest.raises(ValidationError) as exc_info:
        s3.validate_python('anything')

    assert isinstance(exc_info.value.__cause__, BaseExceptionGroup)  # noqa: F821,RUF100  # gated on 3.11+ above
    assert len(exc_info.value.__cause__.exceptions) == 1
    cause = exc_info.value.__cause__.exceptions[0]
    assert cause.__notes__ and cause.__notes__[-1].startswith('\nPydantic: ')
    assert repr(cause) == repr(ValueError('Sub val failure'))
    subcause = cause.__cause__
    assert isinstance(subcause, ValidationError)

    cause_group = subcause.__cause__
    assert isinstance(cause_group, BaseExceptionGroup)  # noqa: F821,RUF100  # gated on 3.11+ above
    assert len(cause_group.exceptions) == 1

    cause = cause_group.exceptions[0]
    assert cause.__notes__
    assert cause.__notes__[-1].startswith('\nPydantic: ')
    assert repr(cause) == repr(ValueError('Oh no!'))
    assert cause.__traceback__ is not None

    sub_cause = cause.__cause__
    assert repr(sub_cause) == repr(AssertionError('Wrong'))
    assert sub_cause.__cause__ is None
    assert sub_cause.__traceback__ is not None


@pytest.mark.skipif(sys.version_info >= (3, 11), reason='This is the backport/legacy version used pre 3.11 only.')
def test_validation_error_cause_contents_legacy():
    from exceptiongroup import BaseExceptionGroup

    enabled_config: CoreConfig = CoreConfig(validation_error_cause=True)

    def multi_raise_py_error(v: Any) -> Any:
        try:
            raise AssertionError('Wrong')
        except AssertionError as e:
            raise ValueError('Oh no!') from e

    s2 = SchemaValidator(core_schema.no_info_plain_validator_function(multi_raise_py_error), config=enabled_config)
    with pytest.raises(ValidationError) as exc_info:
        s2.validate_python('anything')

    cause_group = exc_info.value.__cause__
    assert isinstance(cause_group, BaseExceptionGroup)
    assert len(cause_group.exceptions) == 1

    cause = cause_group.exceptions[0]
    assert repr(cause).startswith("UserWarning('Pydantic: ")

    assert cause.__cause__ is not None
    cause = cause.__cause__
    assert repr(cause) == repr(ValueError('Oh no!'))
    assert cause.__traceback__ is not None

    sub_cause = cause.__cause__
    assert repr(sub_cause) == repr(AssertionError('Wrong'))
    assert sub_cause.__cause__ is None
    assert sub_cause.__traceback__ is not None

    # Make sure a deep inner ValidationError(s) causing a validator failure doesn't cause any problems:
    def outer_raise_py_error(v: Any) -> Any:
        try:
            s2.validate_python('anything')
        except ValidationError as e:
            raise ValueError('Sub val failure') from e

    s3 = SchemaValidator(core_schema.no_info_plain_validator_function(outer_raise_py_error), config=enabled_config)
    with pytest.raises(ValidationError) as exc_info:
        s3.validate_python('anything')

    assert isinstance(exc_info.value.__cause__, BaseExceptionGroup)
    assert len(exc_info.value.__cause__.exceptions) == 1
    cause = exc_info.value.__cause__.exceptions[0]
    assert repr(cause).startswith("UserWarning('Pydantic: ")
    assert cause.__cause__ is not None
    cause = cause.__cause__
    assert repr(cause) == repr(ValueError('Sub val failure'))
    subcause = cause.__cause__
    assert isinstance(subcause, ValidationError)

    cause_group = subcause.__cause__
    assert isinstance(cause_group, BaseExceptionGroup)
    assert len(cause_group.exceptions) == 1

    cause = cause_group.exceptions[0]
    assert repr(cause).startswith("UserWarning('Pydantic: ")
    assert cause.__cause__ is not None
    cause = cause.__cause__
    assert repr(cause) == repr(ValueError('Oh no!'))
    assert cause.__traceback__ is not None

    sub_cause = cause.__cause__
    assert repr(sub_cause) == repr(AssertionError('Wrong'))
    assert sub_cause.__cause__ is None
    assert sub_cause.__traceback__ is not None


class CauseResult(enum.Enum):
    CAUSE = enum.auto()
    NO_CAUSE = enum.auto()
    IMPORT_ERROR = enum.auto()


@pytest.mark.parametrize(
    'desc,config,expected_result',
    [  # Without the backport should still work after 3.10 as not needed:
        (
            'Enabled',
            CoreConfig(validation_error_cause=True),
            CauseResult.CAUSE if sys.version_info >= (3, 11) else CauseResult.IMPORT_ERROR,
        ),
        ('Disabled specifically', CoreConfig(validation_error_cause=False), CauseResult.NO_CAUSE),
        ('Disabled implicitly', {}, CauseResult.NO_CAUSE),
    ],
)
def test_validation_error_cause_config_variants(desc: str, config: CoreConfig, expected_result: CauseResult):
    # Simulate the package being missing:
    with patch.dict('sys.modules', {'exceptiongroup': None}):

        def singular_raise_py_error(v: Any) -> Any:
            raise ValueError('Oh no!')

        s = SchemaValidator(core_schema.no_info_plain_validator_function(singular_raise_py_error), config=config)

        if expected_result is CauseResult.IMPORT_ERROR:
            # Confirm error message contains "requires the exceptiongroup module" in the middle of the string:
            with pytest.raises(ImportError, match='requires the exceptiongroup module'):
                s.validate_python('anything')
        elif expected_result is CauseResult.CAUSE:
            with pytest.raises(ValidationError) as exc_info:
                s.validate_python('anything')
            assert exc_info.value.__cause__ is not None
            assert hasattr(exc_info.value.__cause__, 'exceptions')
            assert len(exc_info.value.__cause__.exceptions) == 1
            assert repr(exc_info.value.__cause__.exceptions[0]) == repr(ValueError('Oh no!'))
        elif expected_result is CauseResult.NO_CAUSE:
            with pytest.raises(ValidationError) as exc_info:
                s.validate_python('anything')
            assert exc_info.value.__cause__ is None
        else:
            raise AssertionError(f'Unhandled result: {expected_result}')


def test_validation_error_cause_traceback_preserved():
    """Makes sure historic bug of traceback being lost is fixed."""

    enabled_config: CoreConfig = CoreConfig(validation_error_cause=True)

    def singular_raise_py_error(v: Any) -> Any:
        raise ValueError('Oh no!')

    s1 = SchemaValidator(core_schema.no_info_plain_validator_function(singular_raise_py_error), config=enabled_config)
    with pytest.raises(ValidationError) as exc_info:
        s1.validate_python('anything')

    base_errs = getattr(exc_info.value.__cause__, 'exceptions', [])
    assert len(base_errs) == 1
    base_err = base_errs[0]

    # Get to the root error:
    cause = base_err
    while cause.__cause__ is not None:
        cause = cause.__cause__

    # Should still have a traceback:
    assert cause.__traceback__ is not None


class BadRepr:
    def __repr__(self):
        raise RuntimeError('bad repr')


def test_error_on_repr(pydantic_version):
    s = SchemaValidator(core_schema.int_schema())
    with pytest.raises(ValidationError) as exc_info:
        s.validate_python(BadRepr())

    assert str(exc_info.value) == (
        '1 validation error for int\n'
        '  Input should be a valid integer '
        '[type=int_type, input_value=<unprintable BadRepr object>, input_type=BadRepr]'
        + (
            f'\n    For further information visit https://errors.pydantic.dev/{pydantic_version}/v/int_type'
            if os.environ.get('PYDANTIC_ERRORS_INCLUDE_URL', '1') != 'false'
            else ''
        )
    )
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': (), 'msg': 'Input should be a valid integer', 'input': IsInstance(BadRepr)}
    ]
    assert exc_info.value.json(include_url=True) == IsJson(
        [
            {
                'type': 'int_type',
                'loc': [],
                'msg': 'Input should be a valid integer',
                'input': '<Unserializable BadRepr object>',
                'url': f'https://errors.pydantic.dev/{pydantic_version}/v/int_type',
            }
        ]
    )


def test_error_json(pydantic_version):
    s = SchemaValidator(core_schema.str_schema(min_length=3))
    with pytest.raises(ValidationError) as exc_info:
        s.validate_python('12')

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_too_short',
            'loc': (),
            'msg': 'String should have at least 3 characters',
            'input': '12',
            'ctx': {'min_length': 3},
        }
    ]
    assert exc_info.value.json() == IsJson(
        [
            {
                'type': 'string_too_short',
                'loc': [],
                'msg': 'String should have at least 3 characters',
                'input': '12',
                'ctx': {'min_length': 3},
                'url': f'https://errors.pydantic.dev/{pydantic_version}/v/string_too_short',
            }
        ]
    )
    assert exc_info.value.json(include_url=False, include_context=False) == IsJson(
        [{'type': 'string_too_short', 'loc': [], 'msg': 'String should have at least 3 characters', 'input': '12'}]
    )
    assert exc_info.value.json().startswith('[{"type":"string_too_short",')
    assert exc_info.value.json(indent=2).startswith('[\n  {\n    "type": "string_too_short",')


def test_error_json_python_error(pydantic_version: str):
    def raise_py_error(v: Any) -> Any:
        try:
            assert False
        except AssertionError as e:
            raise ValueError('Oh no!') from e

    s = SchemaValidator(core_schema.no_info_plain_validator_function(raise_py_error))
    with pytest.raises(ValidationError) as exc_info:
        s.validate_python('anything')

    exc = exc_info.value.errors()[0]['ctx']['error']
    assert isinstance(exc, ValueError)
    assert isinstance(exc.__context__, AssertionError)

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'value_error',
            'loc': (),
            'msg': 'Value error, Oh no!',
            'input': 'anything',
            'ctx': {'error': HasRepr(repr(ValueError('Oh no!')))},
        }
    ]
    assert exc_info.value.json() == IsJson(
        [
            {
                'type': 'value_error',
                'loc': [],
                'msg': 'Value error, Oh no!',
                'input': 'anything',
                'ctx': {'error': 'Oh no!'},
                'url': f'https://errors.pydantic.dev/{pydantic_version}/v/value_error',
            }
        ]
    )
    assert exc_info.value.json(include_url=False, include_context=False) == IsJson(
        [{'type': 'value_error', 'loc': [], 'msg': 'Value error, Oh no!', 'input': 'anything'}]
    )
    assert exc_info.value.json().startswith('[{"type":"value_error",')
    assert exc_info.value.json(indent=2).startswith('[\n  {\n    "type": "value_error",')


def test_error_json_cycle():
    s = SchemaValidator(core_schema.str_schema(min_length=3))
    cycle = []
    cycle.append(cycle)
    msg = '[type=string_type, input_value=[[...]], input_type=list]'
    with pytest.raises(ValidationError, match=re.escape(msg)) as exc_info:
        s.validate_python(cycle)

    assert exc_info.value.json(include_url=False) == IsJson(
        [{'type': 'string_type', 'loc': [], 'msg': 'Input should be a valid string', 'input': ['...']}]
    )


class Foobar:
    pass


class CustomStr:
    def __str__(self):
        return 'custom str'


def test_error_json_unknown():
    s = SchemaValidator(core_schema.str_schema())
    with pytest.raises(ValidationError) as exc_info:
        s.validate_python(Foobar())

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'string_type',
            'loc': (),
            'msg': 'Input should be a valid string',
            'input': HasRepr(IsStr(regex='<.+.test_errors.Foobar object at 0x[a-f0-9]{5,}>', regex_flags=re.I)),
        }
    ]
    # insert_assert(exc_info.value.json(include_url=False))
    assert exc_info.value.json(include_url=False) == IsJson(
        [
            {
                'type': 'string_type',
                'loc': [],
                'msg': 'Input should be a valid string',
                'input': IsStr(regex='<.+.test_errors.Foobar object at 0x[a-f0-9]{5,}>', regex_flags=re.I),
            }
        ]
    )
    with pytest.raises(ValidationError) as exc_info:
        s.validate_python(CustomStr())
    # insert_assert(json.loads(exc_info.value.json(include_url=False)))
    assert exc_info.value.json(include_url=False) == IsJson(
        [{'type': 'string_type', 'loc': [], 'msg': 'Input should be a valid string', 'input': 'custom str'}]
    )


def test_error_json_loc():
    s = SchemaValidator(
        core_schema.dict_schema(core_schema.str_schema(), core_schema.list_schema(core_schema.int_schema()))
    )
    with pytest.raises(ValidationError) as exc_info:
        s.validate_python({'a': [0, 1, 'x'], 'b': [0, 'y']})

    # insert_assert(exc_info.value.json())
    assert exc_info.value.json(include_url=False) == IsJson(
        [
            {
                'type': 'int_parsing',
                'loc': ['a', 2],
                'msg': 'Input should be a valid integer, unable to parse string as an integer',
                'input': 'x',
            },
            {
                'type': 'int_parsing',
                'loc': ['b', 1],
                'msg': 'Input should be a valid integer, unable to parse string as an integer',
                'input': 'y',
            },
        ]
    )


def test_raise_validation_error():
    with pytest.raises(ValidationError, match='1 validation error for Foobar\n') as exc_info:
        raise ValidationError.from_exception_data(
            'Foobar', [{'type': 'greater_than', 'loc': ('a', 2), 'input': 4, 'ctx': {'gt': 5}}]
        )

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'greater_than', 'loc': ('a', 2), 'msg': 'Input should be greater than 5', 'input': 4, 'ctx': {'gt': 5}}
    ]
    with pytest.raises(TypeError, match="GreaterThan: 'gt' required in context"):
        raise ValidationError.from_exception_data('Foobar', [{'type': 'greater_than', 'loc': ('a', 2), 'input': 4}])


@pytest.mark.parametrize(
    'hide_input_in_errors,input_str',
    ((False, 'type=greater_than, input_value=4, input_type=int'), (True, 'type=greater_than')),
)
def test_raise_validation_error_hide_input(hide_input_in_errors, input_str):
    with pytest.raises(ValidationError, match=re.escape(f'Input should be greater than 5 [{input_str}]')):
        raise ValidationError.from_exception_data(
            'Foobar',
            [{'type': 'greater_than', 'loc': ('a', 2), 'input': 4, 'ctx': {'gt': 5}}],
            hide_input=hide_input_in_errors,
        )


def test_raise_validation_error_json():
    with pytest.raises(ValidationError) as exc_info:
        raise ValidationError.from_exception_data('Foobar', [{'type': 'none_required', 'loc': [-42], 'input': 'x'}])

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'none_required', 'loc': (-42,), 'msg': 'Input should be None', 'input': 'x'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        raise ValidationError.from_exception_data(
            'Foobar', [{'type': 'none_required', 'loc': (), 'input': 'x'}], 'json'
        )

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'none_required', 'loc': (), 'msg': 'Input should be null', 'input': 'x'}
    ]


def test_raise_validation_error_custom():
    custom_error = PydanticCustomError(
        'my_error', 'this is a custom error {missed} {foo} {bar}', {'foo': 'X', 'bar': 42}
    )
    with pytest.raises(ValidationError) as exc_info:
        raise ValidationError.from_exception_data('Foobar', [{'type': custom_error, 'input': 'x'}])

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'my_error',
            'loc': (),
            'msg': 'this is a custom error {missed} X 42',
            'input': 'x',
            'ctx': {'foo': 'X', 'bar': 42},
        }
    ]


@pytest.mark.parametrize(
    'msg,result_msg', [('my custom error', 'my custom error'), ('my custom error {foo}', "my custom error {'bar': []}")]
)
def test_raise_validation_error_custom_nested_ctx(msg: str, result_msg: str):
    ctx = {'foo': {'bar': []}}
    custom_error = PydanticCustomError('my_error', msg, ctx)
    with pytest.raises(ValidationError) as exc_info:
        raise ValidationError.from_exception_data('Foobar', [{'type': custom_error, 'input': 'x'}])

    expected_error_detail = {'type': 'my_error', 'loc': (), 'msg': result_msg, 'input': 'x', 'ctx': ctx}

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [expected_error_detail]
    assert exc_info.value.json(include_url=False) == IsJson([{**expected_error_detail, 'loc': []}])


def test_raise_validation_error_known_class_ctx():
    custom_data = Foobar()
    ctx = {'gt': 10, 'foo': {'bar': custom_data}}

    with pytest.raises(ValidationError) as exc_info:
        raise ValidationError.from_exception_data('MyTitle', [{'type': 'greater_than', 'input': 9, 'ctx': ctx}])

    expected_error_detail = {
        'type': 'greater_than',
        'loc': (),
        'msg': 'Input should be greater than 10',
        'input': 9,
        'ctx': ctx,
    }

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [expected_error_detail]
    assert exc_info.value.json(include_url=False) == IsJson(
        [{**expected_error_detail, 'loc': [], 'ctx': {'gt': 10, 'foo': {'bar': str(custom_data)}}}]
    )


def test_raise_validation_error_custom_class_ctx():
    custom_data = Foobar()
    ctx = {'foo': {'bar': custom_data}}
    custom_error = PydanticCustomError('my_error', 'my message', ctx)
    assert custom_error.context == ctx

    with pytest.raises(ValidationError) as exc_info:
        raise ValidationError.from_exception_data('MyTitle', [{'type': custom_error, 'input': 'x'}])

    expected_error_detail = {'type': 'my_error', 'loc': (), 'msg': 'my message', 'input': 'x', 'ctx': ctx}

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [expected_error_detail]
    assert exc_info.value.json(include_url=False) == IsJson(
        [{**expected_error_detail, 'loc': [], 'ctx': {'foo': {'bar': str(custom_data)}}}]
    )


def test_loc_with_dots(pydantic_version):
    v = SchemaValidator(
        core_schema.typed_dict_schema(
            {
                'a': core_schema.typed_dict_field(
                    core_schema.tuple_positional_schema([core_schema.int_schema(), core_schema.int_schema()]),
                    validation_alias='foo.bar',
                )
            }
        )
    )
    assert v.validate_python({'foo.bar': (41, 42)}) == {'a': (41, 42)}
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'foo.bar': ('x', 42)})
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=True) == [
        {
            'type': 'int_parsing',
            'loc': ('foo.bar', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'x',
            'url': f'https://errors.pydantic.dev/{pydantic_version}/v/int_parsing',
        }
    ]
    # insert_assert(str(exc_info.value))
    assert str(exc_info.value) == (
        '1 validation error for typed-dict\n'
        '`foo.bar`.0\n'
        '  Input should be a valid integer, unable to parse string as an integer '
        "[type=int_parsing, input_value='x', input_type=str]"
        + (
            f'\n    For further information visit https://errors.pydantic.dev/{pydantic_version}/v/int_parsing'
            if os.environ.get('PYDANTIC_ERRORS_INCLUDE_URL', '1') != 'false'
            else ''
        )
    )


def test_hide_input_in_error() -> None:
    s = SchemaValidator(core_schema.int_schema())
    with pytest.raises(ValidationError) as exc_info:
        s.validate_python('definitely not an int')

    for error in exc_info.value.errors(include_input=False):
        assert 'input' not in error


def test_hide_input_in_json() -> None:
    s = SchemaValidator(core_schema.int_schema())
    with pytest.raises(ValidationError) as exc_info:
        s.validate_python('definitely not an int')

    for error in exc_info.value.errors(include_input=False):
        assert 'input' not in error


@pytest.mark.skipif(
    sys.version_info < (3, 9) and sys.implementation.name == 'pypy',
    reason='PyPy before 3.9 cannot pickle this correctly',
)
def test_validation_error_pickle() -> None:
    s = SchemaValidator(core_schema.int_schema())
    with pytest.raises(ValidationError) as exc_info:
        s.validate_python('definitely not an int')

    original = exc_info.value
    roundtripped = pickle.loads(pickle.dumps(original))
    assert original.errors() == roundtripped.errors()


def test_errors_include_url() -> None:
    if 'PYDANTIC_ERRORS_INCLUDE_URL' in os.environ:
        raise pytest.skip('cannot test when envvar is set')
    s = SchemaValidator(core_schema.int_schema())
    with pytest.raises(ValidationError) as exc_info:
        s.validate_python('definitely not an int')
    assert 'https://errors.pydantic.dev' in repr(exc_info.value)


@pytest.mark.skipif(sys.platform == 'emscripten', reason='no subprocesses on emscripten')
@pytest.mark.parametrize(
    ('env_var', 'env_var_value', 'expected_to_have_url'),
    [
        ('PYDANTIC_ERRORS_INCLUDE_URL', None, True),
        ('PYDANTIC_ERRORS_INCLUDE_URL', '1', True),
        ('PYDANTIC_ERRORS_INCLUDE_URL', 'True', True),
        ('PYDANTIC_ERRORS_INCLUDE_URL', 'no', False),
        ('PYDANTIC_ERRORS_INCLUDE_URL', '0', False),
        # Legacy environment variable, will raise a deprecation warning:
        ('PYDANTIC_ERRORS_OMIT_URL', '1', False),
        ('PYDANTIC_ERRORS_OMIT_URL', None, True),
    ],
)
def test_errors_include_url_envvar(env_var, env_var_value, expected_to_have_url) -> None:
    """
    Test the `PYDANTIC_ERRORS_INCLUDE_URL` environment variable.

    Since it can only be set before `ValidationError.__repr__()` is first called,
    we need to spawn a subprocess to test it.
    """
    code = "import pydantic_core; from pydantic_core import core_schema; pydantic_core.SchemaValidator(core_schema.int_schema()).validate_python('ooo')"
    env = os.environ.copy()
    # in case the ambient environment has env vars set
    env.pop('PYDANTIC_ERRORS_INCLUDE_URL', None)
    env.pop('PYDANTIC_ERRORS_OMIT_URL', None)
    if env_var_value is not None:
        env[env_var] = env_var_value
    result = subprocess.run(
        [sys.executable, '-W', 'default', '-c', code],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding='utf-8',
        env=env,
    )
    assert result.returncode == 1
    if 'PYDANTIC_ERRORS_OMIT_URL' in env:
        assert 'PYDANTIC_ERRORS_OMIT_URL is deprecated' in result.stdout
    assert ('https://errors.pydantic.dev' in result.stdout) == expected_to_have_url
