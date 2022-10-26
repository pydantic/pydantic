import pytest

from pydantic_core import SchemaValidator, ValidationError


def test_nullable():
    v = SchemaValidator({'type': 'nullable', 'schema': {'type': 'int'}})
    assert v.validate_python(None) is None
    assert v.validate_python(1) == 1
    assert v.validate_python('123') == 123
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('hello')
    assert exc_info.value.errors() == [
        {
            'type': 'int_parsing',
            'loc': (),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'hello',
        }
    ]


def test_union_nullable_bool_int():
    v = SchemaValidator(
        {
            'type': 'union',
            'choices': [
                {'type': 'nullable', 'schema': {'type': 'bool'}},
                {'type': 'nullable', 'schema': {'type': 'int'}},
            ],
        }
    )
    assert v.validate_python(None) is None
    assert v.validate_python(True) is True
    assert v.validate_python(1) == 1
