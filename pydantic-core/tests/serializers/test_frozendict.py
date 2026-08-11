import json
import sys

import pytest

from pydantic_core import PydanticSerializationError, SchemaSerializer
from pydantic_core import core_schema as cs

if sys.version_info < (3, 15):
    pytest.skip(reason='The `frozendict` builtin type is only available in Python 3.15+', allow_module_level=True)
else:
    from builtins import frozendict


def test_frozendict_any():
    s = SchemaSerializer(cs.frozendict_schema())
    output = s.to_python(frozendict({'a': 1, 'b': 2}))
    assert output == frozendict({'a': 1, 'b': 2})
    assert isinstance(output, frozendict)
    assert s.to_python(frozendict({'a': 1}), mode='json') == {'a': 1}
    assert s.to_json(frozendict({'a': 1})) == b'{"a":1}'


def test_frozendict_key_value_schemas():
    s = SchemaSerializer(cs.frozendict_schema(cs.int_schema(), cs.timedelta_schema()))
    from datetime import timedelta

    value = frozendict({1: timedelta(hours=1)})
    output = s.to_python(value)
    assert output == value
    assert isinstance(output, frozendict)
    assert s.to_python(value, mode='json') == {'1': 'PT1H'}
    assert s.to_json(value) == b'{"1":"PT1H"}'


def test_frozendict_include_exclude():
    s = SchemaSerializer(
        cs.frozendict_schema(cs.str_schema(), cs.int_schema(), serialization=cs.filter_dict_schema(exclude={'b'}))
    )
    value = frozendict({'a': 1, 'b': 2, 'c': 3})
    assert s.to_python(value) == frozendict({'a': 1, 'c': 3})
    assert s.to_json(value) == b'{"a":1,"c":3}'


def test_frozendict_fallback():
    s = SchemaSerializer(cs.frozendict_schema())
    with pytest.warns(UserWarning, match='Expected `frozendict.*` - serialized value may not be as expected'):
        assert s.to_python({'a': 1}) == {'a': 1}
    with pytest.warns(UserWarning, match='Expected `frozendict.*` - serialized value may not be as expected'):
        assert s.to_json({'a': 1}) == b'{"a":1}'


def test_frozendict_infer():
    # serialization of a `frozendict` under an `any` schema uses type inference:
    s = SchemaSerializer(cs.any_schema())
    output = s.to_python(frozendict({'a': frozendict({'b': 1})}))
    assert output == frozendict({'a': frozendict({'b': 1})})
    assert isinstance(output, frozendict)
    assert isinstance(output['a'], frozendict)
    assert s.to_python(frozendict({'a': 1}), mode='json') == {'a': 1}
    assert s.to_json(frozendict({'a': 1})) == b'{"a":1}'
    assert json.loads(s.to_json(frozendict({'a': frozendict({'b': 1})}))) == {'a': {'b': 1}}


def test_frozendict_not_valid_as_json_key():
    s = SchemaSerializer(cs.dict_schema(cs.any_schema(), cs.int_schema()))
    with pytest.raises(PydanticSerializationError, match='`frozendict` not valid as object key'):
        s.to_json({frozendict({'a': 1}): 2})
