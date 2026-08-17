import pytest

from pydantic_core import SchemaValidator, ValidationError
from pydantic_core import core_schema as cs


def test_isinstance():
    v = SchemaValidator(cs.int_schema())
    assert v.validate_python(123) == 123
    assert v.isinstance_python(123) is True
    assert v.validate_python('123') == 123
    assert v.isinstance_python('123') is True

    with pytest.raises(ValidationError, match='Input should be a valid integer'):
        v.validate_python('foo')

    assert v.isinstance_python('foo') is False


def test_isinstance_strict():
    v = SchemaValidator(cs.int_schema(strict=True))
    assert v.validate_python(123) == 123
    assert v.isinstance_python(123) is True

    with pytest.raises(ValidationError, match='Input should be a valid integer'):
        v.validate_python('123')

    assert v.isinstance_python('123') is False


def test_isinstance_forbid_extra_fn_override():
    v = SchemaValidator(cs.typed_dict_schema({'f': cs.typed_dict_field(cs.str_schema())}))

    with pytest.raises(ValidationError, match='Extra inputs are not permitted'):
        v.validate_python({'f': 'x', 'extra_field': '123'}, extra='forbid')

    assert v.isinstance_python({'f': 'x', 'extra_field': '123'}, extra='forbid') is False
