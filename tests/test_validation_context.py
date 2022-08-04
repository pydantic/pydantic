import pytest

from pydantic_core import ValidationError

from .conftest import PyAndJson


def test_after(py_and_json: PyAndJson):
    def f(input_value, *, context, **kwargs):
        return input_value + f'| context: {context}'

    v = py_and_json({'type': 'function', 'mode': 'after', 'function': f, 'schema': 'str'})

    assert v.validate_test('foobar') == 'foobar| context: None'
    assert v.validate_test('foobar', None, {1: 10}) == 'foobar| context: {1: 10}'
    assert v.validate_test('foobar', None, 'frogspawn') == 'foobar| context: frogspawn'


def test_mutable_context(py_and_json: PyAndJson):
    def f(input_value, *, context, **kwargs):
        context['foo'] = input_value
        return input_value

    v = py_and_json({'type': 'function', 'mode': 'before', 'function': f, 'schema': 'str'})
    mutable_context = {}
    assert v.validate_test('foobar', None, mutable_context) == 'foobar'
    assert mutable_context == {'foo': 'foobar'}


def test_typed_dict(py_and_json: PyAndJson):
    def f1(input_value, *, context, **kwargs):
        context['f1'] = input_value
        return input_value + f'| context: {context}'

    def f2(input_value, *, context, **kwargs):
        context['f2'] = input_value
        return input_value + f'| context: {context}'

    v = py_and_json(
        {
            'type': 'typed-dict',
            'fields': {
                'f1': {'schema': {'type': 'function', 'mode': 'plain', 'function': f1}},
                'f2': {'schema': {'type': 'function', 'mode': 'plain', 'function': f2}},
            },
        }
    )

    assert v.validate_test({'f1': '1', 'f2': '2'}, None, {'x': 'y'}) == {
        'f1': "1| context: {'x': 'y', 'f1': '1'}",
        'f2': "2| context: {'x': 'y', 'f1': '1', 'f2': '2'}",
    }


def test_wrap(py_and_json: PyAndJson):
    def f(input_value, *, validator, context, **kwargs):
        return validator(input_value) + f'| context: {context}'

    v = py_and_json({'type': 'function', 'mode': 'wrap', 'function': f, 'schema': 'str'})

    assert v.validate_test('foobar') == 'foobar| context: None'
    assert v.validate_test('foobar', None, {1: 10}) == 'foobar| context: {1: 10}'
    assert v.validate_test('foobar', None, 'frogspawn') == 'foobar| context: frogspawn'


def test_isinstance(py_and_json: PyAndJson):
    def f(input_value, *, validator, context, **kwargs):
        if 'error' in context:
            raise ValueError('wrong')
        return validator(input_value)

    v = py_and_json({'type': 'function', 'mode': 'wrap', 'function': f, 'schema': 'str'})

    assert v.validate_python('foobar', None, {}) == 'foobar'

    # internal error!, use generic bit of error message to match both cpython and pypy
    with pytest.raises(TypeError, match='is not iterable'):
        v.validate_test('foobar')

    with pytest.raises(TypeError, match='is not iterable'):
        v.isinstance_test('foobar')

    with pytest.raises(ValidationError, match=r'Value error, wrong \[kind=value_error,'):
        v.validate_test('foobar', None, {'error'})

    assert v.isinstance_test('foobar', None, {}) is True

    with pytest.raises(TypeError, match='is not iterable'):
        v.isinstance_test('foobar')

    assert v.isinstance_test('foobar', None, {'error'}) is False
