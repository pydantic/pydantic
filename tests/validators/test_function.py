import re
from copy import deepcopy

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError


def test_function_before():
    def f(input_value, **kwargs):
        return input_value + ' Changed'

    v = SchemaValidator(
        {'title': 'Test', 'type': 'function', 'mode': 'before', 'function': f, 'schema': {'type': 'str'}}
    )

    assert v.validate_python('input value') == 'input value Changed'


def test_function_before_raise():
    def f(input_value, **kwargs):
        raise ValueError('foobar')

    v = SchemaValidator(
        {'title': 'Test', 'type': 'function', 'mode': 'before', 'function': f, 'schema': {'type': 'str'}}
    )

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python('input value') == 'input value Changed'
    # debug(str(exc_info.value))
    assert exc_info.value.errors() == [
        {'kind': 'value_error', 'loc': [], 'message': 'foobar', 'input_value': 'input value'}
    ]


def test_function_before_error():
    def f(input_value, **kwargs):
        return input_value + 'x'

    v = SchemaValidator(
        {
            'title': 'Test',
            'type': 'function',
            'mode': 'before',
            'function': f,
            'schema': {'type': 'str', 'max_length': 5},
        }
    )

    assert v.validate_python('1234') == '1234x'
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('12345')
    assert exc_info.value.errors() == [
        {
            'kind': 'too_long',
            'loc': [],
            'message': 'String must have at most 5 characters',
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
            'title': 'Test',
            'type': 'function',
            'mode': 'before',
            'function': f,
            'schema': {'type': 'model', 'fields': {'my_field': {'schema': {'type': 'str', 'max_length': 5}}}},
        }
    )

    assert v.validate_python({'my_field': '1234'}) == ({'my_field': '1234x'}, {'my_field'})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'my_field': '12345'})
    assert exc_info.value.errors() == [
        {
            'kind': 'too_long',
            'loc': ['my_field'],
            'message': 'String must have at most 5 characters',
            'input_value': '12345x',
            'context': {'max_length': 5},
        }
    ]


def test_function_wrap():
    def f(input_value, *, validator, **kwargs):
        return validator(input_value) + ' Changed'

    v = SchemaValidator({'title': 'Test', 'type': 'function', 'mode': 'wrap', 'function': f, 'schema': 'str'})

    # with pytest.raises(ValidationError) as exc_info:
    assert v.validate_python('input value') == 'input value Changed'
    # print(exc_info.value)


def test_function_wrap_repr():
    def f(input_value, *, validator, **kwargs):
        return repr(validator)

    v = SchemaValidator({'title': 'Test', 'type': 'function', 'mode': 'wrap', 'function': f, 'schema': 'str'})

    assert v.validate_python('input value') == 'ValidatorCallable(Str(StrValidator))'


def test_function_wrap_str():
    def f(input_value, *, validator, **kwargs):
        return str(validator)

    v = SchemaValidator({'title': 'Test', 'type': 'function', 'mode': 'wrap', 'function': f, 'schema': 'str'})

    assert v.validate_python('input value') == 'ValidatorCallable(Str(StrValidator))'


def test_function_wrap_not_callable():
    with pytest.raises(SchemaError, match='SchemaError: function must be callable'):
        SchemaValidator({'title': 'Test', 'type': 'function', 'mode': 'wrap', 'function': [], 'schema': 'str'})

    with pytest.raises(SchemaError, match='SchemaError: "function" key is required'):
        SchemaValidator({'title': 'Test', 'type': 'function', 'mode': 'wrap', 'schema': 'str'})


def test_wrong_mode():
    with pytest.raises(SchemaError, match='SchemaError: Unexpected function mode "foobar"'):
        SchemaValidator({'title': 'Test', 'type': 'function', 'mode': 'foobar', 'schema': 'str'})


def test_function_after_data():
    f_kwargs = None

    def f(input_value, **kwargs):
        nonlocal f_kwargs
        f_kwargs = deepcopy(kwargs)
        return input_value + ' Changed'

    v = SchemaValidator(
        {
            'title': 'Test',
            'type': 'model',
            'fields': {
                'field_a': {'schema': {'type': 'int'}},
                'field_b': {'schema': {'type': 'function', 'mode': 'after', 'function': f, 'schema': {'type': 'str'}}},
            },
        }
    )

    assert v.validate_python({'field_a': '123', 'field_b': 321}) == (
        {'field_a': 123, 'field_b': '321 Changed'},
        {'field_b', 'field_a'},
    )
    assert f_kwargs == {'data': {'field_a': 123}, 'config': None}


def test_function_after_config():
    f_kwargs = None

    def f(input_value, **kwargs):
        nonlocal f_kwargs
        f_kwargs = deepcopy(kwargs)
        return input_value + ' Changed'

    v = SchemaValidator(
        {
            'title': 'Test',
            'type': 'model',
            'fields': {
                'test_field': {
                    'schema': {'type': 'function', 'mode': 'after', 'function': f, 'schema': {'type': 'str'}}
                }
            },
            'config': {'foo': 'bar'},
        }
    )

    assert v.validate_python({'test_field': 321}) == ({'test_field': '321 Changed'}, {'test_field'})
    assert f_kwargs == {'data': {}, 'config': {'foo': 'bar'}}


def test_config_no_model():
    f_kwargs = None

    def f(input_value, **kwargs):
        nonlocal f_kwargs
        f_kwargs = deepcopy(kwargs)
        return input_value + ' Changed'

    v = SchemaValidator(
        {'type': 'function', 'mode': 'after', 'function': f, 'schema': {'type': 'str'}, 'title': 'Test'}
    )

    assert v.validate_python(123) == '123 Changed'
    assert f_kwargs == {'data': None, 'config': None}


def test_function_plain():
    def f(input_value, **kwargs):
        return input_value * 2

    v = SchemaValidator({'title': 'Test', 'type': 'function', 'mode': 'plain', 'function': f})

    assert v.validate_python(1) == 2
    assert v.validate_python('x') == 'xx'


def test_validate_assignment():
    def f(input_value, **kwargs):
        data, fields_set = input_value
        data['more'] = 'foobar'
        return input_value

    v = SchemaValidator(
        {
            'type': 'function',
            'mode': 'after',
            'function': f,
            'schema': {'type': 'model', 'fields': {'field_a': {'schema': {'type': 'str'}}}},
        }
    )

    m = {'field_a': 'test', 'more': 'foobar'}
    assert v.validate_python({'field_a': 'test'}) == (m, {'field_a'})
    assert v.validate_assignment('field_a', 456, m) == ({'field_a': '456', 'more': 'foobar'}, {'field_a'})


def test_function_wrong_sig():
    def f(input_value):
        return input_value + ' Changed'

    v = SchemaValidator({'type': 'function', 'mode': 'before', 'function': f, 'schema': {'type': 'str'}})
    with pytest.raises(TypeError, match=re.escape("f() got an unexpected keyword argument 'data'")):
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

    f = v.validate_python(1)
    assert isinstance(f, Foobar)
    assert f.a == '11'

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(True)

    assert exc_info.value.errors() == [
        {'kind': 'str_type', 'loc': [], 'message': 'Value must be a valid string', 'input_value': True}
    ]


def test_raise_assertion_error():
    def f(input_value, **kwargs):
        raise AssertionError('foobar')

    v = SchemaValidator({'title': 'Test', 'type': 'function', 'mode': 'before', 'function': f, 'schema': 'str'})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('input value')

    assert exc_info.value.errors() == [
        {'kind': 'assertion_error', 'loc': [], 'message': 'foobar', 'input_value': 'input value'}
    ]


def test_raise_type_error():
    def f(input_value, **kwargs):
        raise TypeError('foobar')

    v = SchemaValidator({'title': 'Test', 'type': 'function', 'mode': 'before', 'function': f, 'schema': 'str'})

    with pytest.raises(TypeError, match='^foobar$'):
        v.validate_python('input value')
