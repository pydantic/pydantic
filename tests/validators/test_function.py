import platform
import re
from copy import deepcopy
from typing import Type

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError

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
            'type': 'value_error',
            'loc': (),
            'msg': 'Value error, foobar',
            'input': 'input value',
            'ctx': {'error': 'foobar'},
        }
    ]


def test_function_before_error():
    def my_function(input_value, **kwargs):
        return input_value + 'x'

    v = SchemaValidator(
        {'type': 'function', 'mode': 'before', 'function': my_function, 'schema': {'type': 'str', 'max_length': 5}}
    )

    assert v.validate_python('1234') == '1234x'
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('12345')
    assert exc_info.value.errors() == [
        {
            'type': 'string_too_long',
            'loc': (),
            'msg': 'String should have at most 5 characters',
            'input': '12345x',
            'ctx': {'max_length': 5},
        }
    ]
    assert repr(exc_info.value).startswith('1 validation error for function-before[my_function(), constrained-str]\n')


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
            'type': 'string_too_long',
            'loc': ('my_field',),
            'msg': 'String should have at most 5 characters',
            'input': '12345x',
            'ctx': {'max_length': 5},
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
            'type': 'int_parsing',
            'loc': (),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'wrong',
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
            'type': 'int_parsing',
            'loc': ('foo',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'wrong',
        }
    ]


def test_function_wrap_invalid_location():
    def f(input_value, *, validator, **kwargs):
        return validator(input_value, ('4',)) + 2

    v = SchemaValidator({'type': 'function', 'mode': 'wrap', 'function': f, 'schema': {'type': 'int'}})

    with pytest.raises(TypeError, match='^ValidatorCallable outer_location must be a str or int$'):
        v.validate_python(4)


def test_wrong_mode():
    with pytest.raises(SchemaError, match=r"function -> mode\s+Input should be 'before' or 'after'"):
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
        {'type': 'string_type', 'loc': (), 'msg': 'Input should be a valid string', 'input': True}
    ]


def test_raise_assertion_error():
    def f(input_value, **kwargs):
        raise AssertionError('foobar')

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': {'type': 'str'}})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('input value')

    assert exc_info.value.errors() == [
        {
            'type': 'assertion_error',
            'loc': (),
            'msg': 'Assertion failed, foobar',
            'input': 'input value',
            'ctx': {'error': 'foobar'},
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
            'type': 'assertion_error',
            'loc': (),
            'msg': 'Assertion failed, Unknown error',
            'input': 'input value',
            'ctx': {'error': 'Unknown error'},
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
