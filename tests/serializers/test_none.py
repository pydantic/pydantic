import pytest

from pydantic_core import SchemaSerializer, core_schema

all_scalars = (
    'int',
    'bool',
    'float',
    'none',
    'str',
    'bytes',
    'datetime',
    'date',
    'time',
    'timedelta',
    'url',
    'multi-host-url',
)
all_types = all_scalars + ('list', 'tuple', 'dict', 'set', 'frozenset')


@pytest.mark.parametrize('schema_type', all_types)
def test_none_fallback(schema_type):
    s = SchemaSerializer({'type': schema_type})
    assert s.to_python(None) is None

    assert s.to_python(None, mode='json') is None

    assert s.to_json(None) == b'null'


@pytest.mark.parametrize('schema_type', all_scalars)
def test_none_fallback_key(schema_type):
    s = SchemaSerializer(core_schema.dict_schema({'type': schema_type}, core_schema.int_schema()))
    assert s.to_python({None: 1}) == {None: 1}

    assert s.to_python({None: 1}, mode='json') == {'None': 1}

    assert s.to_json({None: 1}) == b'{"None":1}'
