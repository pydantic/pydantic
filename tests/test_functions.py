import pytest

from pydantic_core import SchemaValidator, ValidationError


def test_pre_decorator():
    def f(input_value, **kwargs):
        return input_value + ' Changed'

    v = SchemaValidator({'model_name': 'Test', 'type': 'decorator', 'pre_decorator': f, 'field': {'type': 'str'}})

    assert v.run('input value') == 'input value Changed'


def test_pre_decorator_raise():
    def f(input_value, **kwargs):
        raise ValueError('foobar')

    v = SchemaValidator({'model_name': 'Test', 'type': 'decorator', 'pre_decorator': f, 'field': {'type': 'str'}})

    with pytest.raises(ValidationError) as exc_info:
        assert v.run('input value') == 'input value Changed'
    # debug(str(exc_info.value))
    assert exc_info.value.errors() == [
        {
            'kind': 'value_error',
            'loc': [],
            'message': 'foobar',
            'input_value': 'input value',
        },
    ]


def test_wrap_decorator():
    def f(input_value, *, validator, **kwargs):
        return validator(input_value) + ' Changed'

    v = SchemaValidator({'model_name': 'Test', 'type': 'decorator', 'wrap_decorator': f, 'field': {'type': 'str'}})

    # with pytest.raises(ValidationError) as exc_info:
    assert v.run('input value') == 'input value Changed'
    # print(exc_info.value)
