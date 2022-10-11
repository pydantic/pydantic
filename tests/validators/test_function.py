import platform
import re
from copy import deepcopy
from typing import Type

import pytest

from pydantic_core import PydanticCustomError, PydanticErrorKind, SchemaError, SchemaValidator, ValidationError

from ..conftest import plain_repr


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
            'kind': 'too_long',
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
            'kind': 'too_long',
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
        {'kind': 'str_type', 'loc': [], 'message': 'Input should be a valid string', 'input_value': True}
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
    e = PydanticErrorKind('invalid_json', {'error': 'Test'})
    assert e.message() == 'Invalid JSON: Test'
    assert e.kind == 'invalid_json'
    assert e.context == {'error': 'Test'}
    assert str(e) == 'Invalid JSON: Test'
    assert repr(e) == "Invalid JSON: Test [kind=invalid_json, context={'error': 'Test'}]"


def test_pydantic_error_kind_raise_no_ctx():
    def f(input_value, **kwargs):
        raise PydanticErrorKind('finite_number')

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': {'type': 'int'}})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(4)
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'kind': 'finite_number', 'loc': [], 'message': 'Input should be a finite number', 'input_value': 4}
    ]


def test_pydantic_error_kind_raise_ctx():
    def f(input_value, **kwargs):
        raise PydanticErrorKind('greater_than', {'gt': 42})

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
    'kind, message, context, str_e, repr_e',
    [
        ('invalid_input', 'Invalid input', None, 'Invalid input', 'Invalid input [kind=invalid_input, context=None]'),
        (
            'invalid_json',
            'Invalid JSON: foobar',
            {'error': 'foobar'},
            'Invalid JSON: foobar',
            "Invalid JSON: foobar [kind=invalid_json, context={'error': 'foobar'}]",
        ),
        (
            'recursion_loop',
            'Recursion error - cyclic reference detected',
            None,
            'Recursion error - cyclic reference detected',
            'Recursion error - cyclic reference detected [kind=recursion_loop, context=None]',
        ),
        (
            'dict_attributes_type',
            'Input should be a valid dictionary or instance to extract fields from',
            None,
            'Input should be a valid dictionary or instance to extract fields from',
            'Input should be a valid dictionary or instance to extract fields from [kind=dict_attributes_type, context=None]',  # noqa: E501
        ),
        ('missing', 'Field required', None, 'Field required', 'Field required [kind=missing, context=None]'),
        ('frozen', 'Field is frozen', None, 'Field is frozen', 'Field is frozen [kind=frozen, context=None]'),
        (
            'extra_forbidden',
            'Extra inputs are not permitted',
            None,
            'Extra inputs are not permitted',
            'Extra inputs are not permitted [kind=extra_forbidden, context=None]',
        ),
        (
            'invalid_key',
            'Keys should be strings',
            None,
            'Keys should be strings',
            'Keys should be strings [kind=invalid_key, context=None]',
        ),
        (
            'get_attribute_error',
            'Error extracting attribute: foo',
            {'error': 'foo'},
            'Error extracting attribute: foo',
            "Error extracting attribute: foo [kind=get_attribute_error, context={'error': 'foo'}]",
        ),
        (
            'model_class_type',
            'Input should be an instance of foo',
            {'class_name': 'foo'},
            'Input should be an instance of foo',
            "Input should be an instance of foo [kind=model_class_type, context={'class_name': 'foo'}]",
        ),
        (
            'none_required',
            'Input should be None/null',
            None,
            'Input should be None/null',
            'Input should be None/null [kind=none_required, context=None]',
        ),
        (
            'bool',
            'Input should be a valid boolean',
            None,
            'Input should be a valid boolean',
            'Input should be a valid boolean [kind=bool, context=None]',
        ),
        (
            'greater_than',
            'Input should be greater than 42.1',
            {'gt': 42.1},
            'Input should be greater than 42.1',
            "Input should be greater than 42.1 [kind=greater_than, context={'gt': 42.1}]",
        ),
        (
            'greater_than_equal',
            'Input should be greater than or equal to 42.1',
            {'ge': 42.1},
            'Input should be greater than or equal to 42.1',
            "Input should be greater than or equal to 42.1 [kind=greater_than_equal, context={'ge': 42.1}]",
        ),
        (
            'less_than',
            'Input should be less than 42.1',
            {'lt': 42.1},
            'Input should be less than 42.1',
            "Input should be less than 42.1 [kind=less_than, context={'lt': 42.1}]",
        ),
        (
            'less_than_equal',
            'Input should be less than or equal to 42.1',
            {'le': 42.1},
            'Input should be less than or equal to 42.1',
            "Input should be less than or equal to 42.1 [kind=less_than_equal, context={'le': 42.1}]",
        ),
        (
            'less_than_equal',
            'Input should be less than or equal to 42.1',
            {'le': 42.1},
            'Input should be less than or equal to 42.1',
            "Input should be less than or equal to 42.1 [kind=less_than_equal, context={'le': 42.1}]",
        ),
        (
            'too_short',
            'Data should have at least 42 bytes',
            {'min_length': 42},
            'Data should have at least 42 bytes',
            "Data should have at least 42 bytes [kind=too_short, context={'min_length': 42}]",
        ),
        (
            'too_long',
            'Data should have at most 42 bytes',
            {'max_length': 42},
            'Data should have at most 42 bytes',
            "Data should have at most 42 bytes [kind=too_long, context={'max_length': 42}]",
        ),
        (
            'str_type',
            'Input should be a valid string',
            None,
            'Input should be a valid string',
            'Input should be a valid string [kind=str_type, context=None]',
        ),
        (
            'str_unicode',
            'Input should be a valid string, unable to parse raw data as a unicode string',
            None,
            'Input should be a valid string, unable to parse raw data as a unicode string',
            'Input should be a valid string, unable to parse raw data as a unicode string [kind=str_unicode, context=None]',  # noqa: E501
        ),
        (
            'str_pattern_mismatch',
            "String should match pattern 'foo'",
            {'pattern': 'foo'},
            "String should match pattern 'foo'",
            "String should match pattern 'foo' [kind=str_pattern_mismatch, context={'pattern': 'foo'}]",
        ),
        (
            'dict_type',
            'Input should be a valid dictionary',
            None,
            'Input should be a valid dictionary',
            'Input should be a valid dictionary [kind=dict_type, context=None]',
        ),
        (
            'dict_from_mapping',
            'Unable to convert mapping to a dictionary, error: foobar',
            {'error': 'foobar'},
            'Unable to convert mapping to a dictionary, error: foobar',
            "Unable to convert mapping to a dictionary, error: foobar [kind=dict_from_mapping, context={'error': 'foobar'}]",  # noqa: E501
        ),
        (
            'iteration_error',
            'Error iterating over object',
            None,
            'Error iterating over object',
            'Error iterating over object [kind=iteration_error, context=None]',
        ),
        (
            'list_type',
            'Input should be a valid list/array',
            None,
            'Input should be a valid list/array',
            'Input should be a valid list/array [kind=list_type, context=None]',
        ),
        (
            'tuple_type',
            'Input should be a valid tuple',
            None,
            'Input should be a valid tuple',
            'Input should be a valid tuple [kind=tuple_type, context=None]',
        ),
        (
            'set_type',
            'Input should be a valid set',
            None,
            'Input should be a valid set',
            'Input should be a valid set [kind=set_type, context=None]',
        ),
        (
            'bool_type',
            'Input should be a valid boolean',
            None,
            'Input should be a valid boolean',
            'Input should be a valid boolean [kind=bool_type, context=None]',
        ),
        (
            'bool_parsing',
            'Input should be a valid boolean, unable to interpret input',
            None,
            'Input should be a valid boolean, unable to interpret input',
            'Input should be a valid boolean, unable to interpret input [kind=bool_parsing, context=None]',
        ),
        (
            'int_type',
            'Input should be a valid integer',
            None,
            'Input should be a valid integer',
            'Input should be a valid integer [kind=int_type, context=None]',
        ),
        (
            'int_parsing',
            'Input should be a valid integer, unable to parse string as an integer',
            None,
            'Input should be a valid integer, unable to parse string as an integer',
            'Input should be a valid integer, unable to parse string as an integer [kind=int_parsing, context=None]',
        ),
        (
            'int_from_float',
            'Input should be a valid integer, got a number with a fractional part',
            None,
            'Input should be a valid integer, got a number with a fractional part',
            'Input should be a valid integer, got a number with a fractional part [kind=int_from_float, context=None]',
        ),
        (
            'int_nan',
            'Input should be a valid integer, got foo',
            {'nan_value': 'foo'},
            'Input should be a valid integer, got foo',
            "Input should be a valid integer, got foo [kind=int_nan, context={'nan_value': 'foo'}]",
        ),
        (
            'multiple_of',
            'Input should be a multiple of 42.1',
            {'multiple_of': 42.1},
            'Input should be a multiple of 42.1',
            "Input should be a multiple of 42.1 [kind=multiple_of, context={'multiple_of': 42.1}]",
        ),
        (
            'greater_than',
            'Input should be greater than 42.1',
            {'gt': 42.1},
            'Input should be greater than 42.1',
            "Input should be greater than 42.1 [kind=greater_than, context={'gt': 42.1}]",
        ),
        (
            'greater_than_equal',
            'Input should be greater than or equal to 42.1',
            {'ge': 42.1},
            'Input should be greater than or equal to 42.1',
            "Input should be greater than or equal to 42.1 [kind=greater_than_equal, context={'ge': 42.1}]",
        ),
        (
            'less_than',
            'Input should be less than 42.1',
            {'lt': 42.1},
            'Input should be less than 42.1',
            "Input should be less than 42.1 [kind=less_than, context={'lt': 42.1}]",
        ),
        (
            'less_than_equal',
            'Input should be less than or equal to 42.1',
            {'le': 42.1},
            'Input should be less than or equal to 42.1',
            "Input should be less than or equal to 42.1 [kind=less_than_equal, context={'le': 42.1}]",
        ),
        (
            'float_type',
            'Input should be a valid number',
            None,
            'Input should be a valid number',
            'Input should be a valid number [kind=float_type, context=None]',
        ),
        (
            'float_parsing',
            'Input should be a valid number, unable to parse string as an number',
            None,
            'Input should be a valid number, unable to parse string as an number',
            'Input should be a valid number, unable to parse string as an number [kind=float_parsing, context=None]',
        ),
        (
            'finite_number',
            'Input should be a finite number',
            None,
            'Input should be a finite number',
            'Input should be a finite number [kind=finite_number, context=None]',
        ),
        (
            'bytes_type',
            'Input should be a valid bytes',
            None,
            'Input should be a valid bytes',
            'Input should be a valid bytes [kind=bytes_type, context=None]',
        ),
        (
            'value_error',
            'Value error, foobar',
            {'error': 'foobar'},
            'Value error, foobar',
            "Value error, foobar [kind=value_error, context={'error': 'foobar'}]",
        ),
        (
            'assertion_error',
            'Assertion failed, foobar',
            {'error': 'foobar'},
            'Assertion failed, foobar',
            "Assertion failed, foobar [kind=assertion_error, context={'error': 'foobar'}]",
        ),
        (
            'literal_error',
            'Input should be one of: foo',
            {'expected': 'foo'},
            'Input should be one of: foo',
            "Input should be one of: foo [kind=literal_error, context={'expected': 'foo'}]",
        ),
        (
            'date_type',
            'Input should be a valid date',
            None,
            'Input should be a valid date',
            'Input should be a valid date [kind=date_type, context=None]',
        ),
        (
            'date_parsing',
            'Input should be a valid date in the format YYYY-MM-DD, foobar',
            {'error': 'foobar'},
            'Input should be a valid date in the format YYYY-MM-DD, foobar',
            "Input should be a valid date in the format YYYY-MM-DD, foobar [kind=date_parsing, context={'error': 'foobar'}]",  # noqa: E501
        ),
        (
            'date_from_datetime_parsing',
            'Input should be a valid date or datetime, foobar',
            {'error': 'foobar'},
            'Input should be a valid date or datetime, foobar',
            "Input should be a valid date or datetime, foobar [kind=date_from_datetime_parsing, context={'error': 'foobar'}]",  # noqa: E501
        ),
        (
            'date_from_datetime_inexact',
            'Datetimes provided to dates should have zero time - e.g. be exact dates',
            None,
            'Datetimes provided to dates should have zero time - e.g. be exact dates',
            'Datetimes provided to dates should have zero time - e.g. be exact dates [kind=date_from_datetime_inexact, context=None]',  # noqa: E501
        ),
        (
            'time_type',
            'Input should be a valid time',
            None,
            'Input should be a valid time',
            'Input should be a valid time [kind=time_type, context=None]',
        ),
        (
            'time_parsing',
            'Input should be in a valid time format, foobar',
            {'error': 'foobar'},
            'Input should be in a valid time format, foobar',
            "Input should be in a valid time format, foobar [kind=time_parsing, context={'error': 'foobar'}]",
        ),
        (
            'datetime_type',
            'Input should be a valid datetime',
            None,
            'Input should be a valid datetime',
            'Input should be a valid datetime [kind=datetime_type, context=None]',
        ),
        (
            'datetime_parsing',
            'Input should be a valid datetime, foobar',
            {'error': 'foobar'},
            'Input should be a valid datetime, foobar',
            "Input should be a valid datetime, foobar [kind=datetime_parsing, context={'error': 'foobar'}]",
        ),
        (
            'datetime_object_invalid',
            'Invalid datetime object, got foobar',
            {'error': 'foobar'},
            'Invalid datetime object, got foobar',
            "Invalid datetime object, got foobar [kind=datetime_object_invalid, context={'error': 'foobar'}]",
        ),
        (
            'time_delta_type',
            'Input should be a valid timedelta',
            None,
            'Input should be a valid timedelta',
            'Input should be a valid timedelta [kind=time_delta_type, context=None]',
        ),
        (
            'time_delta_parsing',
            'Input should be a valid timedelta, foobar',
            {'error': 'foobar'},
            'Input should be a valid timedelta, foobar',
            "Input should be a valid timedelta, foobar [kind=time_delta_parsing, context={'error': 'foobar'}]",
        ),
        (
            'frozen_set_type',
            'Input should be a valid frozenset',
            None,
            'Input should be a valid frozenset',
            'Input should be a valid frozenset [kind=frozen_set_type, context=None]',
        ),
        (
            'is_instance_of',
            'Input should be an instance of Foo',
            {'class': 'Foo'},
            'Input should be an instance of Foo',
            "Input should be an instance of Foo [kind=is_instance_of, context={'class': 'Foo'}]",
        ),
        (
            'callable_type',
            'Input should be callable',
            None,
            'Input should be callable',
            'Input should be callable [kind=callable_type, context=None]',
        ),
        (
            'union_tag_invalid',
            "Input tag 'foo' found using bar does not match any of the expected tags: baz",
            {'discriminator': 'bar', 'tag': 'foo', 'expected_tags': 'baz'},
            "Input tag 'foo' found using bar does not match any of the expected tags: baz",
            "Input tag 'foo' found using bar does not match any of the expected tags: baz [kind=union_tag_invalid, context={'discriminator': 'bar', 'tag': 'foo', 'expected_tags': 'baz'}]",  # noqa: E501
        ),
        (
            'union_tag_not_found',
            'Unable to extract tag using discriminator foo',
            {'discriminator': 'foo'},
            'Unable to extract tag using discriminator foo',
            "Unable to extract tag using discriminator foo [kind=union_tag_not_found, context={'discriminator': 'foo'}]",  # noqa: E501
        ),
        (
            'arguments_type',
            'Arguments must be a tuple of (positional arguments, keyword arguments) or a plain dict',
            None,
            'Arguments must be a tuple of (positional arguments, keyword arguments) or a plain dict',
            'Arguments must be a tuple of (positional arguments, keyword arguments) or a plain dict [kind=arguments_type, context=None]',  # noqa: E501
        ),
        (
            'unexpected_keyword_argument',
            'Unexpected keyword argument',
            None,
            'Unexpected keyword argument',
            'Unexpected keyword argument [kind=unexpected_keyword_argument, context=None]',
        ),
        (
            'missing_keyword_argument',
            'Missing required keyword argument',
            None,
            'Missing required keyword argument',
            'Missing required keyword argument [kind=missing_keyword_argument, context=None]',
        ),
        (
            'unexpected_positional_argument',
            'Unexpected positional argument',
            None,
            'Unexpected positional argument',
            'Unexpected positional argument [kind=unexpected_positional_argument, context=None]',
        ),
        (
            'missing_positional_argument',
            'Missing required positional argument',
            None,
            'Missing required positional argument',
            'Missing required positional argument [kind=missing_positional_argument, context=None]',
        ),
        (
            'multiple_argument_values',
            'Got multiple values for argument',
            None,
            'Got multiple values for argument',
            'Got multiple values for argument [kind=multiple_argument_values, context=None]',
        ),
    ],
)
def test_error_kind(kind, message, context, str_e, repr_e):
    e = PydanticErrorKind(kind, context)
    assert e.message() == message
    assert e.kind == kind
    assert e.context == context
    assert str(e) == str_e
    assert repr(e) == repr_e
