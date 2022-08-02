import platform
import re
from copy import deepcopy
from typing import Type

import pytest

from pydantic_core import PydanticValueError, SchemaError, SchemaValidator, ValidationError

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
        return validator(input_value) + ' Changed'

    v = SchemaValidator({'type': 'function', 'mode': 'wrap', 'function': f, 'schema': 'str'})

    assert v.validate_python('input value') == 'input value Changed'


def test_function_wrap_repr():
    def f(input_value, *, validator, **kwargs):
        assert repr(validator) == str(validator)
        return plain_repr(validator)

    v = SchemaValidator({'type': 'function', 'mode': 'wrap', 'function': f, 'schema': 'str'})

    assert v.validate_python('input value') == 'ValidatorCallable(Str(StrValidator{strict:false}))'


def test_function_wrap_str():
    def f(input_value, *, validator, **kwargs):
        return plain_repr(validator)

    v = SchemaValidator({'type': 'function', 'mode': 'wrap', 'function': f, 'schema': 'str'})

    assert v.validate_python('input value') == 'ValidatorCallable(Str(StrValidator{strict:false}))'


def test_function_wrap_not_callable():
    with pytest.raises(SchemaError, match='function -> function\n  Input should be callable'):
        SchemaValidator({'type': 'function', 'mode': 'wrap', 'function': [], 'schema': 'str'})

    with pytest.raises(SchemaError, match='function -> function\n  Field required'):
        SchemaValidator({'type': 'function', 'mode': 'wrap', 'schema': 'str'})


def test_wrap_error():
    def f(input_value, *, validator, **kwargs):
        return validator(input_value) * 2

    v = SchemaValidator({'type': 'function', 'mode': 'wrap', 'function': f, 'schema': 'int'})

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


def test_wrong_mode():
    with pytest.raises(SchemaError, match='function -> mode\n  Input should be one of'):
        SchemaValidator({'type': 'function', 'mode': 'foobar', 'schema': 'str'})


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
        SchemaValidator({'type': 'function', 'mode': 'plain', 'function': lambda x: x, 'schema': 'str'})


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

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': 'str'})

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

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': 'str'})

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

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': 'str'})

    with pytest.raises(RuntimeError, match='internal error'):
        v.validate_python('input value')


def test_raise_type_error():
    def f(input_value, **kwargs):
        raise TypeError('foobar')

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': 'str'})

    with pytest.raises(TypeError, match='^foobar$'):
        v.validate_python('input value')


def test_pydantic_value_error():
    e = PydanticValueError(
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
    e = PydanticValueError('my_error', 'this is a custom error {missed}')
    assert e.message() == 'this is a custom error {missed}'
    assert e.message_template == 'this is a custom error {missed}'
    assert e.kind == 'my_error'
    assert e.context is None
    assert str(e) == 'this is a custom error {missed}'
    assert repr(e) == 'this is a custom error {missed} [kind=my_error, context=None]'


def test_pydantic_value_error_usage():
    def f(input_value, **kwargs):
        raise PydanticValueError('my_error', 'this is a custom error {foo} {bar}', {'foo': 'FOOBAR', 'bar': 42})

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
        raise PydanticValueError('my_error', 'this is a custom error {foo}', {(): 'foobar'})

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
        raise PydanticValueError('my_error', 'this is a custom error {foo}', [('foo', 123)])

    v = SchemaValidator({'type': 'function', 'mode': 'plain', 'function': f})

    with pytest.raises(TypeError, match="argument 'context': 'list' object cannot be converted to 'PyDict'"):
        v.validate_python(42)
