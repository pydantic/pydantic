from decimal import Decimal

import pytest

from pydantic_core import PydanticCustomError, PydanticKnownError, PydanticOmit, SchemaValidator, ValidationError
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


def test_pydantic_value_error_none():
    e = PydanticCustomError('my_error', 'this is a custom error {missed}')
    assert e.message() == 'this is a custom error {missed}'
    assert e.message_template == 'this is a custom error {missed}'
    assert e.type == 'my_error'
    assert e.context is None
    assert str(e) == 'this is a custom error {missed}'
    assert repr(e) == 'this is a custom error {missed} [type=my_error, context=None]'


def test_pydantic_value_error_usage():
    def f(input_value, **kwargs):
        raise PydanticCustomError('my_error', 'this is a custom error {foo} {bar}', {'foo': 'FOOBAR', 'bar': 42})

    v = SchemaValidator({'type': 'function', 'mode': 'plain', 'function': f})

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
    def my_function(input_value, **kwargs):
        raise PydanticCustomError('my_error', 'this is a custom error {foo}', {(): 'foobar'})

    v = SchemaValidator({'type': 'function', 'mode': 'plain', 'function': my_function})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(42)

    assert str(exc_info.value) == (
        '1 validation error for function-plain[my_function()]\n'
        "  (error rendering message: TypeError: 'tuple' object cannot be converted to 'PyString') "
        '[type=my_error, input_value=42, input_type=int]'
    )
    with pytest.raises(TypeError, match="'tuple' object cannot be converted to 'PyString'"):
        exc_info.value.errors()


def test_pydantic_value_error_invalid_type():
    def f(input_value, **kwargs):
        raise PydanticCustomError('my_error', 'this is a custom error {foo}', [('foo', 123)])

    v = SchemaValidator({'type': 'function', 'mode': 'plain', 'function': f})

    with pytest.raises(TypeError, match="argument 'context': 'list' object cannot be converted to 'PyDict'"):
        v.validate_python(42)


def test_validator_instance_plain():
    class CustomValidator:
        def __init__(self):
            self.foo = 42
            self.bar = 'before'

        def validate(self, input_value, **kwargs):
            return f'{input_value} {self.foo} {self.bar}'

    c = CustomValidator()
    v = SchemaValidator({'type': 'function', 'mode': 'plain', 'metadata': {'instance': c}, 'function': c.validate})
    c.foo += 1

    assert v.validate_python('input value') == 'input value 43 before'
    c.bar = 'changed'
    assert v.validate_python('input value') == 'input value 43 changed'


def test_validator_instance_after():
    class CustomValidator:
        def __init__(self):
            self.foo = 42

        def validate(self, input_value, **kwargs):
            assert isinstance(input_value, str)
            return f'{input_value} {self.foo}'

    c = CustomValidator()
    v = SchemaValidator(
        {
            'type': 'function',
            'mode': 'after',
            'metadata': {'instance': c},
            'function': c.validate,
            'schema': {'type': 'str'},
        }
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


def test_pydantic_error_type_raise_no_ctx():
    def f(input_value, **kwargs):
        raise PydanticKnownError('finite_number')

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': {'type': 'int'}})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(4)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'finite_number', 'loc': (), 'msg': 'Input should be a finite number', 'input': 4}
    ]


def test_pydantic_error_type_raise_ctx():
    def f(input_value, **kwargs):
        raise PydanticKnownError('greater_than', {'gt': 42})

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': {'type': 'int'}})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(4)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'greater_than', 'loc': (), 'msg': 'Input should be greater than 42', 'input': 4, 'ctx': {'gt': 42.0}}
    ]


all_errors = [
    ('json_invalid', 'Invalid JSON: foobar', {'error': 'foobar'}),
    ('json_type', 'JSON input should be string, bytes or bytearray', None),
    ('recursion_loop', 'Recursion error - cyclic reference detected', None),
    ('dict_attributes_type', 'Input should be a valid dictionary or instance to extract fields from', None),
    ('missing', 'Field required', None),
    ('frozen', 'Field is frozen', None),
    ('extra_forbidden', 'Extra inputs are not permitted', None),
    ('invalid_key', 'Keys should be strings', None),
    ('get_attribute_error', 'Error extracting attribute: foo', {'error': 'foo'}),
    ('model_class_type', 'Input should be an instance of foo', {'class_name': 'foo'}),
    ('none_required', 'Input should be None/null', None),
    ('bool', 'Input should be a valid boolean', None),
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
    ('string_too_long', 'String should have at most 42 characters', {'max_length': 42}),
    ('dict_type', 'Input should be a valid dictionary', None),
    ('mapping_type', 'Input should be a valid mapping, error: foobar', {'error': 'foobar'}),
    ('iterable_type', 'Input should be iterable', None),
    ('iteration_error', 'Error iterating over object, error: foobar', {'error': 'foobar'}),
    ('list_type', 'Input should be a valid list/array', None),
    ('tuple_type', 'Input should be a valid tuple', None),
    ('set_type', 'Input should be a valid set', None),
    ('bool_type', 'Input should be a valid boolean', None),
    ('bool_parsing', 'Input should be a valid boolean, unable to interpret input', None),
    ('int_type', 'Input should be a valid integer', None),
    ('int_parsing', 'Input should be a valid integer, unable to parse string as an integer', None),
    ('int_from_float', 'Input should be a valid integer, got a number with a fractional part', None),
    ('multiple_of', 'Input should be a multiple of 42.1', {'multiple_of': 42.1}),
    ('greater_than', 'Input should be greater than 42.1', {'gt': 42.1}),
    ('greater_than_equal', 'Input should be greater than or equal to 42.1', {'ge': 42.1}),
    ('less_than', 'Input should be less than 42.1', {'lt': 42.1}),
    ('less_than_equal', 'Input should be less than or equal to 42.1', {'le': 42.1}),
    ('float_type', 'Input should be a valid number', None),
    ('float_parsing', 'Input should be a valid number, unable to parse string as an number', None),
    ('bytes_type', 'Input should be a valid bytes', None),
    ('bytes_too_short', 'Data should have at least 42 bytes', {'min_length': 42}),
    ('bytes_too_long', 'Data should have at most 42 bytes', {'max_length': 42}),
    ('value_error', 'Value error, foobar', {'error': 'foobar'}),
    ('assertion_error', 'Assertion failed, foobar', {'error': 'foobar'}),
    ('literal_error', 'Input should be foo', {'expected': 'foo'}),
    ('literal_error', 'Input should be foo or bar', {'expected': 'foo or bar'}),
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
    ('datetime_object_invalid', 'Invalid datetime object, got foobar', {'error': 'foobar'}),
    ('datetime_past', 'Datetime should be in the past', None),
    ('datetime_future', 'Datetime should be in the future', None),
    ('datetime_aware', 'Datetime should have timezone info', None),
    ('datetime_naive', 'Datetime should not have timezone info', None),
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
    ('positional_arguments_type', 'Positional arguments must be a list or tuple', None),
    ('keyword_arguments_type', 'Keyword arguments must be a dictionary', None),
    ('unexpected_keyword_argument', 'Unexpected keyword argument', None),
    ('missing_keyword_argument', 'Missing required keyword argument', None),
    ('unexpected_positional_argument', 'Unexpected positional argument', None),
    ('missing_positional_argument', 'Missing required positional argument', None),
    ('multiple_argument_values', 'Got multiple values for argument', None),
    ('url_type', 'URL input should be a string or URL', None),
    ('url_parsing', 'Input should be a valid URL, Foobar', {'error': 'Foobar'}),
    ('url_syntax_violation', 'Input violated strict URL syntax rules, Foobar', {'error': 'Foobar'}),
    ('url_too_long', 'URL should have at most 42 characters', {'max_length': 42}),
    ('url_scheme', 'URL scheme should be "foo", "bar" or "spam"', {'expected_schemes': '"foo", "bar" or "spam"'}),
]


@pytest.mark.parametrize('error_type, message, context', all_errors)
def test_error_type(error_type, message, context):
    e = PydanticKnownError(error_type, context)
    assert e.message() == message
    assert e.type == error_type
    assert e.context == context


def test_all_errors_covered():
    listed_types = set(error_type for error_type, *_ in all_errors)
    actual_types = {e['type'] for e in list_all_errors()}
    assert actual_types == listed_types


def test_error_decimal():
    e = PydanticKnownError('greater_than', {'gt': Decimal('42.1')})
    assert e.message() == 'Input should be greater than 42.1'
    assert e.type == 'greater_than'
    assert e.context == {'gt': 42.1}


def test_custom_error_decimal():
    e = PydanticCustomError('my_error', 'this is a custom error {foobar}', {'foobar': Decimal('42.010')})
    assert e.message() == 'this is a custom error 42.010'
    assert e.message_template == 'this is a custom error {foobar}'
    assert e.type == 'my_error'
    assert e.context == {'foobar': Decimal('42.010')}


def test_pydantic_value_error_plain(py_and_json: PyAndJson):
    def f(input_value, **kwargs):
        raise PydanticCustomError

    v = py_and_json({'type': 'function', 'mode': 'plain', 'function': f})
    with pytest.raises(TypeError, match='missing 2 required positional arguments'):
        v.validate_test('4')


@pytest.mark.parametrize('exception', [PydanticOmit(), PydanticOmit])
def test_list_omit_exception(py_and_json: PyAndJson, exception):
    def f(input_value, **kwargs):
        if input_value % 2 == 0:
            raise exception
        return input_value

    v = py_and_json(
        {
            'type': 'list',
            'items_schema': {'type': 'function', 'schema': {'type': 'int'}, 'mode': 'after', 'function': f},
        }
    )
    assert v.validate_test([1, 2, '3', '4']) == [1, 3]


def test_omit_exc_repr():
    assert repr(PydanticOmit()) == 'PydanticOmit()'
    assert str(PydanticOmit()) == 'PydanticOmit()'


def test_type_error_error():
    with pytest.raises(TypeError, match="^GreaterThan: 'gt' context value must be a Number$"):
        PydanticKnownError('greater_than', {'gt': []})


def test_does_not_require_context():
    with pytest.raises(TypeError, match="^'json_type' errors do not require context$"):
        PydanticKnownError('json_type', {'gt': 123})
