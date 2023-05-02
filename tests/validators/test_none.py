import pytest

from pydantic_core import SchemaValidator, ValidationError


def test_python_none():
    v = SchemaValidator({'type': 'none'})
    assert v.validate_python(None) is None
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(1)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'none_required', 'loc': (), 'msg': 'Input should be None', 'input': 1}
    ]


def test_json_none():
    v = SchemaValidator({'type': 'none'})
    assert v.validate_json('null') is None
    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('1')
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'none_required', 'loc': (), 'msg': 'Input should be null', 'input': 1}
    ]
