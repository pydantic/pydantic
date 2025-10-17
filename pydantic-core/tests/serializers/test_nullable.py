import pytest

from pydantic_core import SchemaSerializer, core_schema


def test_nullable():
    s = SchemaSerializer(core_schema.nullable_schema(core_schema.int_schema()))
    assert s.to_python(None) is None
    assert s.to_python(1) == 1
    assert s.to_python(None, mode='json') is None
    assert s.to_python(1, mode='json') == 1
    assert s.to_json(1) == b'1'
    assert s.to_json(None) == b'null'
    with pytest.warns(
        UserWarning,
        match=r"Expected `int` - serialized value may not be as expected \[input_value='aaa', input_type=str\]",
    ):
        assert s.to_json('aaa') == b'"aaa"'
