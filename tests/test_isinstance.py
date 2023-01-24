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


def test_isinstance_json():
    v = SchemaValidator({'type': 'int'})
    assert v.validate_json('123') == 123
    assert v.isinstance_json('123') is True
    assert v.validate_json('"123"') == 123
    assert v.isinstance_json('"123"') is True

    with pytest.raises(ValidationError, match='Input should be a valid integer'):
        v.validate_json('"foo"')

    assert v.isinstance_json('"foo"') is False

    with pytest.raises(ValidationError, match=r'Invalid JSON: expected value at line 1 column 1 \[type=json_invalid,'):
        v.validate_json('x')

    # invalid json returns False, not an error!
    assert v.isinstance_json('x') is False


def test_internal_error():
    v = SchemaValidator(
        {
            'type': 'model',
            'cls': int,
            'schema': {'type': 'typed-dict', 'return_fields_set': True, 'fields': {'f': {'schema': {'type': 'int'}}}},
        }
    )
    with pytest.raises(AttributeError, match="'int' object has no attribute '__dict__'"):
        v.validate_python({'f': 123})

    with pytest.raises(AttributeError, match="'int' object has no attribute '__dict__'"):
        v.validate_json('{"f": 123}')

    with pytest.raises(AttributeError, match="'int' object has no attribute '__dict__'"):
        v.isinstance_python({'f': 123})

    with pytest.raises(AttributeError, match="'int' object has no attribute '__dict__'"):
        v.isinstance_json('{"f": 123}')


def test_omit(py_and_json: PyAndJson):
    def omit(v, **kwargs):
        if v == 'omit':
            raise PydanticOmit
        elif v == 'error':
            raise ValueError('error')
        else:
            return v

    v = py_and_json(core_schema.function_plain_schema(omit))
    assert v.validate_test('foo') == 'foo'
    assert v.isinstance_test('foo') is True

    assert v.isinstance_test('error') is False
    with pytest.raises(SchemaError, match='Uncaught Omit error, please check your usage of `default` validators.'):
        v.validate_test('omit')
