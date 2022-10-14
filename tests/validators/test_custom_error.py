import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema

from ..conftest import PyAndJson


def test_custom_error(py_and_json: PyAndJson):
    v = py_and_json(
        core_schema.custom_error_schema(core_schema.int_schema(), 'foobar', custom_error_message='Hello there')
    )
    assert v.validate_test(1) == 1

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test('foobar')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [{'kind': 'foobar', 'loc': [], 'message': 'Hello there', 'input_value': 'foobar'}]


def test_custom_error_kind(py_and_json: PyAndJson):
    v = py_and_json(core_schema.custom_error_schema(core_schema.int_schema(), 'recursion_loop'))
    assert v.validate_test(1) == 1

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test('X')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'kind': 'recursion_loop',
            'loc': [],
            'message': 'Recursion error - cyclic reference detected',
            'input_value': 'X',
        }
    ]


def test_custom_error_error():
    with pytest.raises(SchemaError, match=r'custom_error_kind\s+Field required \[kind=missing'):
        SchemaValidator({'type': 'custom_error', 'schema': {'type': 'int'}})


def test_custom_error_invalid():
    with pytest.raises(SchemaError, match='custom_error_message should not be provided if kind matches a known error'):
        SchemaValidator(
            core_schema.custom_error_schema(core_schema.int_schema(), 'recursion_loop', custom_error_message='xxx')
        )
