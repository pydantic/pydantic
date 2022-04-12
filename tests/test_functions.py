from copy import deepcopy

import pytest

from pydantic_core import SchemaValidator, ValidationError


def test_function_before():
    def f(input_value, **kwargs):
        return input_value + ' Changed'

    v = SchemaValidator({'title': 'Test', 'type': 'function-before', 'function': f, 'field': {'type': 'str'}})

    assert v.run('input value') == 'input value Changed'


def test_function_before_raise():
    def f(input_value, **kwargs):
        raise ValueError('foobar')

    v = SchemaValidator({'title': 'Test', 'type': 'function-before', 'function': f, 'field': {'type': 'str'}})

    with pytest.raises(ValidationError) as exc_info:
        assert v.run('input value') == 'input value Changed'
    # debug(str(exc_info.value))
    assert exc_info.value.errors() == [
        {'kind': 'value_error', 'loc': [], 'message': 'foobar', 'input_value': 'input value'}
    ]


def test_function_wrap():
    def f(input_value, *, validator, **kwargs):
        return validator(input_value) + ' Changed'

    v = SchemaValidator({'title': 'Test', 'type': 'function-wrap', 'function': f, 'field': {'type': 'str'}})

    # with pytest.raises(ValidationError) as exc_info:
    assert v.run('input value') == 'input value Changed'
    # print(exc_info.value)


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
                'field_a': {'type': 'int'},
                'field_b': {'type': 'function-after', 'function': f, 'field': {'type': 'str'}},
            },
        }
    )

    assert v.run({'field_a': '123', 'field_b': 321}) == (
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
            'fields': {'test_field': {'type': 'function-after', 'function': f, 'field': {'type': 'str'}}},
            'config': {'foo': 'bar'},
        }
    )

    assert v.run({'test_field': 321}) == ({'test_field': '321 Changed'}, {'test_field'})
    assert f_kwargs == {'data': {}, 'config': {'foo': 'bar'}}


def test_config_no_model():
    f_kwargs = None

    def f(input_value, **kwargs):
        nonlocal f_kwargs
        f_kwargs = deepcopy(kwargs)
        return input_value + ' Changed'

    v = SchemaValidator({'type': 'function-after', 'function': f, 'field': {'type': 'str'}, 'title': 'Test'})

    assert v.run(123) == '123 Changed'
    assert f_kwargs == {'data': {}, 'config': None}


def test_function_plain():
    def f(input_value, **kwargs):
        return input_value * 2

    v = SchemaValidator({'title': 'Test', 'type': 'function-plain', 'function': f})

    assert v.run(1) == 2
    assert v.run('x') == 'xx'
