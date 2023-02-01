import pytest

from pydantic_core import SchemaValidator, ValidationError, core_schema


def test_lax_or_strict():
    v = SchemaValidator(core_schema.lax_or_strict_schema(core_schema.str_schema(), core_schema.int_schema()))
    # validator is default - lax so with no runtime arg, we're in lax mode, and we use the string validator
    assert v.validate_python('aaa') == 'aaa'
    # the strict validator is itself lax
    assert v.validate_python(b'aaa') == 'aaa'
    # in strict mode
    assert v.validate_python(123, strict=True) == 123
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('123', strict=True)

    # location is not changed
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'int_type', 'loc': (), 'msg': 'Input should be a valid integer', 'input': '123'}
    ]


def test_lax_or_strict_default_strict():
    v = SchemaValidator(
        core_schema.lax_or_strict_schema(core_schema.str_schema(), core_schema.int_schema(), strict=True)
    )
    assert v.validate_python('aaa', strict=False) == 'aaa'
    assert v.validate_python(b'aaa', strict=False) == 'aaa'
    # in strict mode
    assert v.validate_python(123) == 123
    assert v.validate_python(123, strict=True) == 123
    # the int validator isn't strict since it wasn't configured that way and strictness wasn't overridden at runtime
    assert v.validate_python('123') == 123

    # but it is if we set `strict` to True
    with pytest.raises(ValidationError, match='Input should be a valid integer'):
        v.validate_python('123', strict=True)
