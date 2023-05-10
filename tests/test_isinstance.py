import pytest

from pydantic_core import PydanticOmit, SchemaError, SchemaValidator, ValidationError, core_schema

from .conftest import PyAndJson


def test_isinstance():
    v = SchemaValidator({'type': 'int'})
    assert v.validate_python(123) == 123
    assert v.isinstance_python(123) is True
    assert v.validate_python('123') == 123
    assert v.isinstance_python('123') is True

    with pytest.raises(ValidationError, match='Input should be a valid integer'):
        v.validate_python('foo')

    assert v.isinstance_python('foo') is False


def test_isinstance_strict():
    v = SchemaValidator({'type': 'int', 'strict': True})
    assert v.validate_python(123) == 123
    assert v.isinstance_python(123) is True

    with pytest.raises(ValidationError, match='Input should be a valid integer'):
        v.validate_python('123')

    assert v.isinstance_python('123') is False


def test_internal_error():
    v = SchemaValidator(
        {
            'type': 'model',
            'cls': int,
            'schema': {'type': 'model-fields', 'fields': {'f': {'type': 'model-field', 'schema': {'type': 'int'}}}},
        }
    )
    with pytest.raises(AttributeError, match="'int' object has no attribute '__dict__'"):
        v.validate_python({'f': 123})

    with pytest.raises(AttributeError, match="'int' object has no attribute '__dict__'"):
        v.validate_json('{"f": 123}')

    with pytest.raises(AttributeError, match="'int' object has no attribute '__dict__'"):
        v.isinstance_python({'f': 123})


def test_omit(py_and_json: PyAndJson):
    def omit(v, info):
        if v == 'omit':
            raise PydanticOmit
        elif v == 'error':
            raise ValueError('error')
        else:
            return v

    v = py_and_json(core_schema.general_plain_validator_function(omit))
    assert v.validate_test('foo') == 'foo'
    if v.validator_type == 'python':
        assert v.isinstance_test('foo') is True

    if v.validator_type == 'python':
        assert v.isinstance_test('error') is False
    with pytest.raises(SchemaError, match='Uncaught Omit error, please check your usage of `default` validators.'):
        v.validate_test('omit')
