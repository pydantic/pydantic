import pytest

from pydantic_core import SchemaValidator, ValidationError, core_schema

from .conftest import PyAndJson


def test_after(py_and_json: PyAndJson):
    def f(input_value, info):
        return input_value + f'| context: {info.context}'

    v = py_and_json(core_schema.with_info_after_validator_function(f, core_schema.str_schema()))

    assert v.validate_test('foobar') == 'foobar| context: None'
    assert v.validate_test('foobar', None, {1: 10}) == 'foobar| context: {1: 10}'
    assert v.validate_test('foobar', None, 'frogspawn') == 'foobar| context: frogspawn'


def test_mutable_context(py_and_json: PyAndJson):
    def f(input_value, info):
        info.context['foo'] = input_value
        return input_value

    v = py_and_json(core_schema.with_info_before_validator_function(f, core_schema.str_schema()))
    mutable_context = {}
    assert v.validate_test('foobar', None, mutable_context) == 'foobar'
    assert mutable_context == {'foo': 'foobar'}


def test_typed_dict(py_and_json: PyAndJson):
    def f1(input_value, info):
        info.context['f1'] = input_value
        return input_value + f'| context: {info.context}'

    def f2(input_value, info):
        info.context['f2'] = input_value
        return input_value + f'| context: {info.context}'

    v = py_and_json(
        core_schema.typed_dict_schema(
            {
                'f1': core_schema.typed_dict_field(core_schema.with_info_plain_validator_function(f1)),
                'f2': core_schema.typed_dict_field(core_schema.with_info_plain_validator_function(f2)),
            }
        )
    )

    assert v.validate_test({'f1': '1', 'f2': '2'}, None, {'x': 'y'}) == {
        'f1': "1| context: {'x': 'y', 'f1': '1'}",
        'f2': "2| context: {'x': 'y', 'f1': '1', 'f2': '2'}",
    }


def test_wrap(py_and_json: PyAndJson):
    def f(input_value, validator, info):
        return validator(input_value) + f'| context: {info.context}'

    v = py_and_json(core_schema.with_info_wrap_validator_function(f, core_schema.str_schema()))

    assert v.validate_test('foobar') == 'foobar| context: None'
    assert v.validate_test('foobar', None, {1: 10}) == 'foobar| context: {1: 10}'
    assert v.validate_test('foobar', None, 'frogspawn') == 'foobar| context: frogspawn'


def test_isinstance(py_and_json: PyAndJson):
    def f(input_value, validator, info):
        if 'error' in info.context:
            raise ValueError('wrong')
        return validator(input_value)

    v = py_and_json(core_schema.with_info_wrap_validator_function(f, core_schema.str_schema()))

    assert v.validate_python('foobar', None, {}) == 'foobar'

    # internal error!, use generic bit of error message to match both cpython and pypy
    with pytest.raises(TypeError, match='is not iterable'):
        v.validate_test('foobar')

    with pytest.raises(TypeError, match='is not iterable'):
        v.isinstance_test('foobar')

    with pytest.raises(ValidationError, match=r'Value error, wrong \[type=value_error,'):
        v.validate_test('foobar', None, {'error'})

    assert v.isinstance_test('foobar', None, {}) is True

    with pytest.raises(TypeError, match='is not iterable'):
        v.isinstance_test('foobar')

    assert v.isinstance_test('foobar', None, {'error'}) is False


def test_validate_assignment_with_context():
    def f1(input_value, info):
        info.context['f1'] = input_value
        return input_value + f'| context: {info.context}'

    def f2(input_value, info):
        info.context['f2'] = input_value
        return input_value + f'| context: {info.context}'

    v = SchemaValidator(
        core_schema.model_fields_schema(
            {
                'f1': core_schema.model_field(core_schema.with_info_plain_validator_function(f1)),
                'f2': core_schema.model_field(core_schema.with_info_plain_validator_function(f2)),
            }
        )
    )

    m1, model_extra, fields_set = v.validate_python({'f1': '1', 'f2': '2'}, strict=None, context={'x': 'y'})
    assert m1 == {'f1': "1| context: {'x': 'y', 'f1': '1'}", 'f2': "2| context: {'x': 'y', 'f1': '1', 'f2': '2'}"}
    assert model_extra is None
    assert fields_set == {'f1', 'f2'}

    m2, model_extra, fields_set = v.validate_assignment(m1, 'f1', '3', context={'x': 'y'})
    assert m2 == {'f1': "3| context: {'x': 'y', 'f1': '3'}", 'f2': "2| context: {'x': 'y', 'f1': '1', 'f2': '2'}"}
    assert model_extra is None
    assert fields_set == {'f1'}
