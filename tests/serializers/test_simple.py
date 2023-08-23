import json
from enum import IntEnum

import pytest

from pydantic_core import SchemaSerializer, core_schema

try:
    import numpy
except ImportError:
    numpy = None


class IntSubClass(int):
    pass


class MyIntEnum(IntEnum):
    one = 1
    two = 2


class FloatSubClass(float):
    pass


# A number well outside of i64 range
_BIG_NUMBER_BYTES = b'1' + (b'0' * 40)


@pytest.mark.parametrize('custom_type_schema', [None, 'any'])
@pytest.mark.parametrize(
    'schema_type,value,expected_python,expected_json',
    [
        ('int', 1, 1, b'1'),
        ('int', int(_BIG_NUMBER_BYTES), int(_BIG_NUMBER_BYTES), _BIG_NUMBER_BYTES),
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


def test_int_to_float():
    """
    See https://github.com/pydantic/pydantic-core/pull/866
    """
    s = SchemaSerializer(core_schema.float_schema())
    v_plain = s.to_python(1)
    assert v_plain == 1
    assert type(v_plain) == int

    v_plain_subclass = s.to_python(IntSubClass(1))
    assert v_plain_subclass == IntSubClass(1)
    assert type(v_plain_subclass) == IntSubClass

    v_json = s.to_python(1, mode='json')
    assert v_json == 1.0
    assert type(v_json) == float

    v_json_subclass = s.to_python(IntSubClass(1), mode='json')
    assert v_json_subclass == 1
    assert type(v_json_subclass) == float

    assert s.to_json(1) == b'1.0'
    assert s.to_json(IntSubClass(1)) == b'1.0'


def test_int_to_float_key():
    """
    See https://github.com/pydantic/pydantic-core/pull/866
    """
    s = SchemaSerializer(core_schema.dict_schema(core_schema.float_schema(), core_schema.float_schema()))
    v_plain = s.to_python({1: 1})
    assert v_plain == {1: 1}
    assert type(list(v_plain.keys())[0]) == int
    assert type(v_plain[1]) == int

    v_json = s.to_python({1: 1}, mode='json')
    assert v_json == {'1': 1.0}
    assert type(v_json['1']) == float

    assert s.to_json({1: 1}) == b'{"1":1.0}'


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


@pytest.mark.skipif(numpy is None, reason='numpy is not installed')
def test_numpy():
    s = SchemaSerializer(core_schema.float_schema())
    v = s.to_python(numpy.float64(1.0))
    assert v == 1.0
    assert type(v) == numpy.float64

    v = s.to_python(numpy.float64(1.0), mode='json')
    assert v == 1.0
    assert type(v) == float

    assert s.to_json(numpy.float64(1.0)) == b'1.0'
