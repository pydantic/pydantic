import json
from collections import Counter
from datetime import timedelta

import pytest

from pydantic_core import SchemaSerializer
from pydantic_core import core_schema as cs


def test_counter_any() -> None:
    s = SchemaSerializer(cs.counter_schema())
    output = s.to_python(Counter({'a': 1, 'b': 2}))
    assert output == Counter({'a': 1, 'b': 2})
    assert type(output) is Counter
    assert s.to_python(Counter({'a': 1}), mode='json') == {'a': 1}
    assert type(s.to_python(Counter({'a': 1}), mode='json')) is dict
    assert s.to_json(Counter({'a': 1})) == b'{"a":1}'


def test_counter_values_preserved() -> None:
    # zero and negative counts are kept as is:
    s = SchemaSerializer(cs.counter_schema(cs.str_schema(), cs.int_schema()))
    value = Counter({'a': 3, 'b': 0, 'c': -2})
    assert dict(s.to_python(value)) == {'a': 3, 'b': 0, 'c': -2}
    assert s.to_python(value, mode='json') == {'a': 3, 'b': 0, 'c': -2}
    assert s.to_json(value) == b'{"a":3,"b":0,"c":-2}'


def test_counter_key_value_schemas() -> None:
    s = SchemaSerializer(cs.counter_schema(cs.int_schema(), cs.timedelta_schema()))

    value = Counter({1: timedelta(hours=1)})
    output = s.to_python(value)
    assert output == value
    assert type(output) is Counter
    assert s.to_python(value, mode='json') == {'1': 'PT1H'}
    assert s.to_json(value) == b'{"1":"PT1H"}'


def test_counter_include_exclude() -> None:
    s = SchemaSerializer(
        cs.counter_schema(cs.str_schema(), cs.int_schema(), serialization=cs.filter_dict_schema(exclude={'b'}))
    )
    value = Counter({'a': 1, 'b': 2, 'c': 3})
    assert s.to_python(value) == Counter({'a': 1, 'c': 3})
    assert s.to_json(value) == b'{"a":1,"c":3}'
    assert s.to_python(value, exclude={'c'}) == Counter({'a': 1})
    assert s.to_json(value, include={'a'}) == b'{"a":1}'


def test_counter_subclass() -> None:
    class MyCounter(Counter):
        pass

    s = SchemaSerializer(cs.counter_schema(cs.str_schema(), cs.int_schema()))
    output = s.to_python(MyCounter({'a': 1}))
    assert output == Counter({'a': 1})
    assert type(output) is Counter
    assert s.to_json(MyCounter({'a': 1})) == b'{"a":1}'


def test_counter_fallback() -> None:
    s = SchemaSerializer(cs.counter_schema())
    with pytest.warns(UserWarning, match='Expected `counter.*` - serialized value may not be as expected'):
        output = s.to_python({'a': 1})
    assert output == {'a': 1}
    assert type(output) is dict
    with pytest.warns(UserWarning, match='Expected `counter.*` - serialized value may not be as expected'):
        assert s.to_json({'a': 1}) == b'{"a":1}'


def test_counter_infer() -> None:
    # serialization of a `Counter` under an `any` schema uses type inference:
    s = SchemaSerializer(cs.any_schema())
    output = s.to_python(Counter({'a': Counter({'b': 1})}))
    assert output == Counter({'a': Counter({'b': 1})})
    assert type(output) is Counter
    assert type(output['a']) is Counter
    assert s.to_python(Counter({'a': 1}), mode='json') == {'a': 1}
    assert type(s.to_python(Counter({'a': 1}), mode='json')) is dict
    assert s.to_json(Counter({'a': 1})) == b'{"a":1}'
    assert json.loads(s.to_json(Counter({'a': Counter({'b': 1})}))) == {'a': {'b': 1}}


def test_counter_from_dict_serializer() -> None:
    # a `dict` schema still accepts a `Counter` (as a `dict` subclass):
    s = SchemaSerializer(cs.dict_schema(cs.str_schema(), cs.int_schema()))
    output = s.to_python(Counter({'a': 1}))
    assert output == {'a': 1}
    assert type(output) is dict
