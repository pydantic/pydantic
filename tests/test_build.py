import pytest

from pydantic_core import SchemaError, SchemaValidator


def test_build_error_type():
    with pytest.raises(SchemaError, match='Unknown schema type: "foobar"'):
        SchemaValidator({'type': 'foobar', 'title': 'TestModel'})


def test_build_error_internal():
    msg = (
        'Error building "str" validator:\n'
        '  TypeError: \'str\' object cannot be interpreted as an integer'  # noqa Q003
    )
    with pytest.raises(SchemaError, match=msg):
        SchemaValidator({'type': 'str', 'min_length': 'xxx', 'title': 'TestModel'})


def test_build_error_deep():
    msg = (
        'Error building "model" validator:\n'
        '  SchemaError: Key "age":\n'
        '  SchemaError: Error building "int" validator:\n'
        '  TypeError: \'str\' object cannot be interpreted as an integer'  # noqa Q003
    )
    with pytest.raises(SchemaError, match=msg):
        SchemaValidator({'title': 'MyTestModel', 'type': 'model', 'fields': {'age': {'type': 'int', 'ge': 'not-int'}}})


def test_schema_as_string():
    v = SchemaValidator('bool')
    assert v.validate_python('tRuE') is True


def test_schema_wrong_type():
    v = SchemaValidator('bool')
    assert v.validate_python('tRuE') is True
