import pytest

from pydantic_core import SchemaError, SchemaValidator


def test_build_error_type():
    with pytest.raises(SchemaError, match='Unknown schema type: "foobar"'):
        SchemaValidator({'type': 'foobar', 'title': 'TestModel'})


def test_build_error_internal():
    msg = (
        'Error building "str-constrained" validator:\n'
        '  TypeError: \'str\' object cannot be interpreted as an integer'  # noqa Q003
    )
    with pytest.raises(SchemaError, match=msg):
        SchemaValidator({'type': 'str-constrained', 'min_length': 'xxx', 'title': 'TestModel'})


def test_build_error_deep():
    msg = (
        'Error building "model" validator:\n'
        '  SchemaError: Error building "int-constrained" validator:\n'
        '  TypeError: \'str\' object cannot be interpreted as an integer'  # noqa Q003
    )
    with pytest.raises(SchemaError, match=msg):
        SchemaValidator(
            {'title': 'MyTestModel', 'type': 'model', 'fields': {'age': {'type': 'int-constrained', 'ge': 'not-int'}}}
        )
