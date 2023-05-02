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
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'foobar', 'loc': (), 'msg': 'Hello there', 'input': 'foobar'}
    ]


def test_custom_error_type(py_and_json: PyAndJson):
    v = py_and_json(core_schema.custom_error_schema(core_schema.int_schema(), 'recursion_loop'))
    assert v.validate_test(1) == 1

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test('X')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'recursion_loop', 'loc': (), 'msg': 'Recursion error - cyclic reference detected', 'input': 'X'}
    ]


def test_custom_error_error():
    with pytest.raises(SchemaError, match=r'custom_error_type\s+Field required \[type=missing'):
        SchemaValidator({'type': 'custom-error', 'schema': {'type': 'int'}})


def test_custom_error_invalid():
    msg = "custom_error_message should not be provided if 'custom_error_type' matches a known error"
    with pytest.raises(SchemaError, match=msg):
        SchemaValidator(
            core_schema.custom_error_schema(core_schema.int_schema(), 'recursion_loop', custom_error_message='xxx')
        )
