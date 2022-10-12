import platform
import re
from copy import deepcopy
from typing import Type

import pytest

from pydantic_core import (
    PydanticCustomError,
    PydanticKindError,
    PydanticOmit,
    SchemaError,
    SchemaValidator,
    ValidationError,
)

from ..conftest import PyAndJson, plain_repr


def test_function_before():
    def f(input_value, **kwargs):
        return input_value + ' Changed'

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': {'type': 'str'}})

    assert v.validate_python('input value') == 'input value Changed'


def test_function_before_raise():
    def f(input_value, **kwargs):
        raise ValueError('foobar')

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': {'type': 'str'}})

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python('input value') == 'input value Changed'
    # debug(str(exc_info.value))
    assert exc_info.value.errors() == [
        {
            'kind': 'value_error',
            'loc': [],
            'message': 'Value error, foobar',
            'input_value': 'input value',
            'context': {'error': 'foobar'},
        }
    ]


def test_function_before_error():
    def f(input_value, **kwargs):
        return input_value + 'x'

    v = SchemaValidator(
        {'type': 'function', 'mode': 'before', 'function': f, 'schema': {'type': 'str', 'max_length': 5}}
    )

    assert v.validate_python('1234') == '1234x'
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('12345')
    assert exc_info.value.errors() == [
        {
            'kind': 'string_too_long',
            'loc': [],
            'message': 'String should have at most 5 characters',
            'input_value': '12345x',
            'context': {'max_length': 5},
        }
    ]


def test_function_before_error_model():
    def f(input_value, **kwargs):
        if 'my_field' in input_value:
            input_value['my_field'] += 'x'
        return input_value

    v = SchemaValidator(
        {
            'type': 'function',
            'mode': 'before',
            'function': f,
            'schema': {'type': 'typed-dict', 'fields': {'my_field': {'schema': {'type': 'str', 'max_length': 5}}}},
        }
    )

    assert v.validate_python({'my_field': '1234'}) == {'my_field': '1234x'}
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'my_field': '12345'})
    assert exc_info.value.errors() == [
        {
            'kind': 'string_too_long',
            'loc': ['my_field'],
            'message': 'String should have at most 5 characters',
            'input_value': '12345x',
            'context': {'max_length': 5},
        }
    ]


def test_function_wrap():
    def f(input_value, *, validator, **kwargs):
        return validator(input_value=input_value) + ' Changed'

    v = SchemaValidator({'type': 'function', 'mode': 'wrap', 'function': f, 'schema': {'type': 'str'}})

    assert v.validate_python('input value') == 'input value Changed'


def test_function_wrap_repr():
    def f(input_value, *, validator, **kwargs):
        assert repr(validator) == str(validator)
        return plain_repr(validator)

    v = SchemaValidator({'type': 'function', 'mode': 'wrap', 'function': f, 'schema': {'type': 'str'}})

    assert v.validate_python('input value') == 'ValidatorCallable(Str(StrValidator{strict:false}))'


def test_function_wrap_str():
    def f(input_value, *, validator, **kwargs):
        return plain_repr(validator)

    v = SchemaValidator({'type': 'function', 'mode': 'wrap', 'function': f, 'schema': {'type': 'str'}})

    assert v.validate_python('input value') == 'ValidatorCallable(Str(StrValidator{strict:false}))'


def test_function_wrap_not_callable():
    with pytest.raises(SchemaError, match='function-wrap -> function\n  Input should be callable'):
        SchemaValidator({'type': 'function', 'mode': 'wrap', 'function': [], 'schema': {'type': 'str'}})

    with pytest.raises(SchemaError, match='function-wrap -> function\n  Field required'):
        SchemaValidator({'type': 'function', 'mode': 'wrap', 'schema': {'type': 'str'}})


def test_wrap_error():
    def f(input_value, *, validator, **kwargs):
        try:
            return validator(input_value) * 2
        except ValidationError as e:
            assert e.title == 'ValidatorCallable'
            assert str(e).startswith('1 validation error for ValidatorCallable\n')
            raise e

    v = SchemaValidator({'type': 'function', 'mode': 'wrap', 'function': f, 'schema': {'type': 'int'}})

    assert v.validate_python('42') == 84
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('wrong')
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': [],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'wrong',
        }
    ]


def test_function_wrap_location():
    def f(input_value, *, validator, **kwargs):
        return validator(input_value, outer_location='foo') + 2

    v = SchemaValidator({'type': 'function', 'mode': 'wrap', 'function': f, 'schema': {'type': 'int'}})

    assert v.validate_python(4) == 6
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('wrong')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': ['foo'],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'wrong',
        }
    ]


def test_function_wrap_invalid_location():
    def f(input_value, *, validator, **kwargs):
        return validator(input_value, ('4',)) + 2

    v = SchemaValidator({'type': 'function', 'mode': 'wrap', 'function': f, 'schema': {'type': 'int'}})

    with pytest.raises(TypeError, match='^ValidatorCallable outer_location must be a str or int$'):
        v.validate_python(4)


def test_wrong_mode():
    with pytest.raises(SchemaError, match='function -> mode\n  Input should be one of'):
        SchemaValidator({'type': 'function', 'mode': 'foobar', 'schema': {'type': 'str'}})


def test_function_after_data():
    f_kwargs = None

    def f(input_value, **kwargs):
        nonlocal f_kwargs
        f_kwargs = deepcopy(kwargs)
        return input_value + ' Changed'

    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'field_a': {'schema': {'type': 'int'}},
                'field_b': {'schema': {'type': 'function', 'mode': 'after', 'function': f, 'schema': {'type': 'str'}}},
            },
        }
    )

    assert v.validate_python({'field_a': '123', 'field_b': b'321'}) == {'field_a': 123, 'field_b': '321 Changed'}
    assert f_kwargs == {'data': {'field_a': 123}, 'config': None, 'context': None}


def test_function_after_config():
    f_kwargs = None

    def f(input_value, **kwargs):
        nonlocal f_kwargs
        f_kwargs = deepcopy(kwargs)
        return input_value + ' Changed'

    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'test_field': {
                    'schema': {'type': 'function', 'mode': 'after', 'function': f, 'schema': {'type': 'str'}}
                }
            },
        },
        {'config_choose_priority': 2},
    )

    assert v.validate_python({'test_field': b'321'}) == {'test_field': '321 Changed'}
    assert f_kwargs == {'data': {}, 'config': {'config_choose_priority': 2}, 'context': None}


def test_config_no_model():
    f_kwargs = None

    def f(input_value, **kwargs):
        nonlocal f_kwargs
        f_kwargs = deepcopy(kwargs)
        return input_value + ' Changed'

    v = SchemaValidator({'type': 'function', 'mode': 'after', 'function': f, 'schema': {'type': 'str'}})

    assert v.validate_python(b'abc') == 'abc Changed'
    assert f_kwargs == {'data': None, 'config': None, 'context': None}


def test_function_plain():
    def f(input_value, **kwargs):
        return input_value * 2

    v = SchemaValidator({'type': 'function', 'mode': 'plain', 'function': f})

    assert v.validate_python(1) == 2
    assert v.validate_python('x') == 'xx'


def test_plain_with_schema():
    with pytest.raises(SchemaError, match='function-plain -> schema\n  Extra inputs are not permitted'):
        SchemaValidator({'type': 'function', 'mode': 'plain', 'function': lambda x: x, 'schema': {'type': 'str'}})


def test_validate_assignment():
    def f(input_value, **kwargs):
        input_value['more'] = 'foobar'
        return input_value

    v = SchemaValidator(
        {
            'type': 'function',
            'mode': 'after',
            'function': f,
            'schema': {'type': 'typed-dict', 'fields': {'field_a': {'schema': {'type': 'str'}}}},
        }
    )

    m = {'field_a': 'test', 'more': 'foobar'}
    assert v.validate_python({'field_a': 'test'}) == m
    assert v.validate_assignment('field_a', b'abc', m) == {'field_a': 'abc', 'more': 'foobar'}


def test_function_wrong_sig():
    def f(input_value):
        return input_value + ' Changed'

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': {'type': 'str'}})

    # exception messages differ between python and pypy
    if platform.python_implementation() == 'PyPy':
        error_message = 'f() got 3 unexpected keyword arguments'
    else:
        error_message = "f() got an unexpected keyword argument 'data'"

    with pytest.raises(TypeError, match=re.escape(error_message)):
        v.validate_python('input value')


def test_class_with_validator():
    class Foobar:
        a: int

        def __init__(self, a):
            self.a = a

        @classmethod
        def __validate__(cls, input_value, **kwargs):
            return Foobar(input_value * 2)

    v = SchemaValidator(
        {'type': 'function', 'mode': 'after', 'function': Foobar.__validate__, 'schema': {'type': 'str'}}
    )

    f = v.validate_python('foo')
    assert isinstance(f, Foobar)
    assert f.a == 'foofoo'

    f = v.validate_python(b'a')
    assert isinstance(f, Foobar)
    assert f.a == 'aa'

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(True)

    assert exc_info.value.errors() == [
        {'kind': 'string_type', 'loc': [], 'message': 'Input should be a valid string', 'input_value': True}
    ]


def test_raise_assertion_error():
    def f(input_value, **kwargs):
        raise AssertionError('foobar')

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': {'type': 'str'}})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('input value')

    assert exc_info.value.errors() == [
        {
            'kind': 'assertion_error',
            'loc': [],
            'message': 'Assertion failed, foobar',
            'input_value': 'input value',
            'context': {'error': 'foobar'},
        }
    ]


def test_raise_assertion_error_plain():
    def f(input_value, **kwargs):
        raise AssertionError

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': {'type': 'str'}})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('input value')

    assert exc_info.value.errors() == [
        {
            'kind': 'assertion_error',
            'loc': [],
            'message': 'Assertion failed, Unknown error',
            'input_value': 'input value',
            'context': {'error': 'Unknown error'},
        }
    ]


@pytest.mark.parametrize('base_error', [ValueError, AssertionError])
def test_error_with_error(base_error: Type[Exception]):
    class MyError(base_error):
        def __str__(self):
            raise RuntimeError('internal error')

    def f(input_value, **kwargs):
        raise MyError()

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': {'type': 'str'}})

    with pytest.raises(RuntimeError, match='internal error'):
        v.validate_python('input value')


def test_raise_type_error():
    def f(input_value, **kwargs):
        raise TypeError('foobar')

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': {'type': 'str'}})

    with pytest.raises(TypeError, match='^foobar$'):
        v.validate_python('input value')


def test_pydantic_value_error():
    e = PydanticCustomError(
        'my_error', 'this is a custom error {missed} {foo} {bar} {spam}', {'foo': 'X', 'bar': 42, 'spam': []}
    )
    assert e.message() == 'this is a custom error {missed} X 42 []'
    assert e.message_template == 'this is a custom error {missed} {foo} {bar} {spam}'
    assert e.kind == 'my_error'
    assert e.context == {'foo': 'X', 'bar': 42, 'spam': []}
    assert str(e) == 'this is a custom error {missed} X 42 []'
    assert repr(e) == (
        "this is a custom error {missed} X 42 [] [kind=my_error, context={'foo': 'X', 'bar': 42, 'spam': []}]"
    )


def test_pydantic_value_error_none():
    e = PydanticCustomError('my_error', 'this is a custom error {missed}')
    assert e.message() == 'this is a custom error {missed}'
    assert e.message_template == 'this is a custom error {missed}'
    assert e.kind == 'my_error'
    assert e.context is None
    assert str(e) == 'this is a custom error {missed}'
    assert repr(e) == 'this is a custom error {missed} [kind=my_error, context=None]'


def test_pydantic_value_error_usage():
    def f(input_value, **kwargs):
        raise PydanticCustomError('my_error', 'this is a custom error {foo} {bar}', {'foo': 'FOOBAR', 'bar': 42})

    v = SchemaValidator({'type': 'function', 'mode': 'plain', 'function': f})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(42)

    assert exc_info.value.errors() == [
        {
            'kind': 'my_error',
            'loc': [],
            'message': 'this is a custom error FOOBAR 42',
            'input_value': 42,
            'context': {'foo': 'FOOBAR', 'bar': 42},
        }
    ]


def test_pydantic_value_error_invalid_dict():
    def f(input_value, **kwargs):
        raise PydanticCustomError('my_error', 'this is a custom error {foo}', {(): 'foobar'})

    v = SchemaValidator({'type': 'function', 'mode': 'plain', 'function': f})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(42)

    assert str(exc_info.value) == (
        '1 validation error for function-plain\n'
        "  (error rendering message: TypeError: 'tuple' object cannot be converted to 'PyString') "
        '[kind=my_error, input_value=42, input_type=int]'
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
    v = SchemaValidator({'type': 'function', 'mode': 'plain', 'validator_instance': c, 'function': c.validate})
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
            'validator_instance': c,
            'function': c.validate,
            'schema': {'type': 'str'},
        }
    )
    c.foo += 1

    assert v.validate_python('input value') == 'input value 43'
    assert v.validate_python(b'is bytes') == 'is bytes 43'


def test_pydantic_error_kind():
    e = PydanticKindError('invalid_json', {'error': 'Test'})
    assert e.message() == 'Invalid JSON: Test'
    assert e.kind == 'invalid_json'
    assert e.context == {'error': 'Test'}
    assert str(e) == 'Invalid JSON: Test'
    assert repr(e) == "Invalid JSON: Test [kind=invalid_json, context={'error': 'Test'}]"


def test_pydantic_error_kind_raise_no_ctx():
    def f(input_value, **kwargs):
        raise PydanticKindError('finite_number')

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': {'type': 'int'}})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(4)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'kind': 'finite_number', 'loc': [], 'message': 'Input should be a finite number', 'input_value': 4}
    ]


def test_pydantic_error_kind_raise_ctx():
    def f(input_value, **kwargs):
        raise PydanticKindError('greater_than', {'gt': 42})

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': {'type': 'int'}})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(4)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'greater_than',
            'loc': [],
            'message': 'Input should be greater than 42',
            'input_value': 4,
            'context': {'gt': 42.0},
        }
    ]


@pytest.mark.parametrize(
    'kind, message, context',
    [
        ('invalid_json', 'Invalid JSON: foobar', {'error': 'foobar'}),
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
        ('string_unicode', 'Input should be a valid string, unable to parse raw data as a unicode string', None),
        ('string_pattern_mismatch', "String should match pattern 'foo'", {'pattern': 'foo'}),
        ('string_too_short', 'String should have at least 42 characters', {'min_length': 42}),
        ('string_too_long', 'String should have at most 42 characters', {'max_length': 42}),
        ('dict_type', 'Input should be a valid dictionary', None),
        ('dict_from_mapping', 'Unable to convert mapping to a dictionary, error: foobar', {'error': 'foobar'}),
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
        ('literal_single_error', 'Input should be: foo', {'expected': 'foo'}),
        ('literal_multiple_error', 'Input should be one of: foo,bar', {'expected': 'foo,bar'}),
        ('date_type', 'Input should be a valid date', None),
        ('date_parsing', 'Input should be a valid date in the format YYYY-MM-DD, foobar', {'error': 'foobar'}),
        ('date_from_datetime_parsing', 'Input should be a valid date or datetime, foobar', {'error': 'foobar'}),
        ('date_from_datetime_inexact', 'Datetimes provided to dates should have zero time - e.g. be exact dates', None),
        ('time_type', 'Input should be a valid time', None),
        ('time_parsing', 'Input should be in a valid time format, foobar', {'error': 'foobar'}),
        ('datetime_type', 'Input should be a valid datetime', None),
        ('datetime_parsing', 'Input should be a valid datetime, foobar', {'error': 'foobar'}),
        ('datetime_object_invalid', 'Invalid datetime object, got foobar', {'error': 'foobar'}),
        ('time_delta_type', 'Input should be a valid timedelta', None),
        ('time_delta_parsing', 'Input should be a valid timedelta, foobar', {'error': 'foobar'}),
        ('frozen_set_type', 'Input should be a valid frozenset', None),
        ('is_instance_of', 'Input should be an instance of Foo', {'class': 'Foo'}),
        ('callable_type', 'Input should be callable', None),
        (
            'union_tag_invalid',
            "Input tag 'foo' found using bar does not match any of the expected tags: baz",
            {'discriminator': 'bar', 'tag': 'foo', 'expected_tags': 'baz'},
        ),
        ('union_tag_not_found', 'Unable to extract tag using discriminator foo', {'discriminator': 'foo'}),
        (
            'arguments_type',
            'Arguments must be a tuple of (positional arguments, keyword arguments) or a plain dict',
            None,
        ),
        ('unexpected_keyword_argument', 'Unexpected keyword argument', None),
        ('missing_keyword_argument', 'Missing required keyword argument', None),
        ('unexpected_positional_argument', 'Unexpected positional argument', None),
        ('missing_positional_argument', 'Missing required positional argument', None),
        ('multiple_argument_values', 'Got multiple values for argument', None),
    ],
)
def test_error_kind(kind, message, context):
    e = PydanticKindError(kind, context)
    assert e.message() == message
    assert e.kind == kind
    assert e.context == context


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
