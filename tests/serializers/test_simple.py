import json
from enum import IntEnum

import pytest

from pydantic_core import SchemaSerializer


class IntSubClass(int):
    pass


class MyIntEnum(IntEnum):
    one = 1
    two = 2


class FloatSubClass(float):
    pass


@pytest.mark.parametrize('custom_type_schema', [None, 'any'])
@pytest.mark.parametrize(
    'schema_type,value,expected_python,expected_json',
    [
        ('int', 1, 1, b'1'),
        ('bool', True, True, b'true'),
        ('bool', False, False, b'false'),
        ('float', 1.0, 1.0, b'1.0'),
        ('float', 42.31415, 42.31415, b'42.31415'),
        ('none', None, None, b'null'),
        ('int', IntSubClass(42), IntSubClass(42), b'42'),
        ('int', MyIntEnum.one, MyIntEnum.one, b'1'),
        ('float', FloatSubClass(42), FloatSubClass(42), b'42.0'),
    ],
)
def test_simple_serializers(schema_type, value, expected_python, expected_json, custom_type_schema):
    if custom_type_schema is None:
        schema = {'type': schema_type}
    else:
        schema = {'type': custom_type_schema}

    s = SchemaSerializer(schema)
    v = s.to_python(value)
    assert v == expected_python
    assert type(v) == type(expected_python)

    assert s.to_json(value) == expected_json

    v_json = s.to_python(value, mode='json')
    v_json_expected = json.loads(expected_json)
    assert v_json == v_json_expected
    assert type(v_json) == type(v_json_expected)


@pytest.mark.parametrize('schema_type', ['int', 'bool', 'float', 'none'])
def test_simple_serializers_fallback(schema_type):
    s = SchemaSerializer({'type': schema_type})
    with pytest.warns(
        UserWarning, match=f'Expected `{schema_type}` but got `list` - serialized value may not be as expected'
    ):
        assert s.to_python([1, 2, 3]) == [1, 2, 3]

    with pytest.warns(
        UserWarning, match=f'Expected `{schema_type}` but got `list` - serialized value may not be as expected'
    ):
        assert s.to_python([1, 2, b'bytes'], mode='json') == [1, 2, 'bytes']

    with pytest.warns(
        UserWarning, match=f'Expected `{schema_type}` but got `list` - serialized value may not be as expected'
    ):
        assert s.to_json([1, 2, 3]) == b'[1,2,3]'
