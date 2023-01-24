import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema

from ..conftest import PyAndJson, plain_repr


def test_custom_error(py_and_json: PyAndJson):
    v = py_and_json(
        core_schema.custom_error_schema(core_schema.int_schema(), 'foobar', custom_error_message='Hello there')
    )
    assert v.validate_test(1) == 1

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test('foobar')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [{'type': 'foobar', 'loc': (), 'msg': 'Hello there', 'input': 'foobar'}]


def test_custom_error_type(py_and_json: PyAndJson):
    v = py_and_json(core_schema.custom_error_schema(core_schema.int_schema(), 'recursion_loop'))
    assert v.validate_test(1) == 1

    with pytest.raises(ValidationError) as exc_info:
        v.validate_test('X')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
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


def test_ask():
    class MyModel:
        # this is not required, but it avoids `__fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__fields_set__'
        field_a: str
        field_b: int

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'custom-error',
                'custom_error_type': 'foobar',
                'custom_error_message': 'Hello there',
                'schema': {
                    'type': 'typed-dict',
                    'return_fields_set': True,
                    'fields': {'field_a': {'schema': {'type': 'str'}}, 'field_b': {'schema': {'type': 'int'}}},
                },
            },
        }
    )
    assert 'expect_fields_set:true' in plain_repr(v)
    m = v.validate_python({'field_a': 'test', 'field_b': 12})
    assert isinstance(m, MyModel)
    assert m.field_a == 'test'
    assert m.field_b == 12
    assert m.__fields_set__ == {'field_a', 'field_b'}
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'field_a': 'test'})
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'foobar', 'loc': (), 'msg': 'Hello there', 'input': {'field_a': 'test'}}
    ]
