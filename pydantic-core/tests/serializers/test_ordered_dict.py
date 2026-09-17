import json
from collections import OrderedDict
from datetime import timedelta

import pytest

from pydantic_core import SchemaSerializer
from pydantic_core import core_schema as cs


def test_ordered_dict_any() -> None:
    s = SchemaSerializer(cs.ordered_dict_schema())
    output = s.to_python(OrderedDict({'a': 1, 'b': 2}))
    assert output == OrderedDict({'a': 1, 'b': 2})
    assert type(output) is OrderedDict
    assert s.to_python(OrderedDict({'a': 1}), mode='json') == {'a': 1}
    assert type(s.to_python(OrderedDict({'a': 1}), mode='json')) is dict
    assert s.to_json(OrderedDict({'a': 1})) == b'{"a":1}'


def test_ordered_dict_order_preserved() -> None:
    """Iterating over an `OrderedDict` using the `dict` C API doesn't account for reorderings."""
    s = SchemaSerializer(cs.ordered_dict_schema(cs.str_schema(), cs.int_schema()))
    value = OrderedDict([('a', 1), ('b', 2), ('c', 3)])
    value.move_to_end('a')

    assert list(s.to_python(value).items()) == [('b', 2), ('c', 3), ('a', 1)]
    assert list(s.to_python(value, mode='json').items()) == [('b', 2), ('c', 3), ('a', 1)]
    assert s.to_json(value) == b'{"b":2,"c":3,"a":1}'


def test_ordered_dict_key_value_schemas() -> None:
    s = SchemaSerializer(cs.ordered_dict_schema(cs.int_schema(), cs.timedelta_schema()))

    value = OrderedDict({1: timedelta(hours=1)})
    output = s.to_python(value)
    assert output == value
    assert type(output) is OrderedDict
    assert s.to_python(value, mode='json') == {'1': 'PT1H'}
    assert s.to_json(value) == b'{"1":"PT1H"}'


def test_ordered_dict_include_exclude() -> None:
    s = SchemaSerializer(
        cs.ordered_dict_schema(cs.str_schema(), cs.int_schema(), serialization=cs.filter_dict_schema(exclude={'b'}))
    )
    value = OrderedDict({'a': 1, 'b': 2, 'c': 3})
    assert s.to_python(value) == OrderedDict({'a': 1, 'c': 3})
    assert s.to_json(value) == b'{"a":1,"c":3}'
    assert s.to_python(value, exclude={'c'}) == OrderedDict({'a': 1})
    assert s.to_json(value, include={'a'}) == b'{"a":1}'


def test_ordered_dict_subclass() -> None:
    class MyOrderedDict(OrderedDict):
        pass

    s = SchemaSerializer(cs.ordered_dict_schema(cs.str_schema(), cs.int_schema()))
    output = s.to_python(MyOrderedDict({'a': 1}))
    assert output == OrderedDict({'a': 1})
    assert type(output) is OrderedDict
    assert s.to_json(MyOrderedDict({'a': 1})) == b'{"a":1}'


def test_ordered_dict_fallback() -> None:
    s = SchemaSerializer(cs.ordered_dict_schema())
    with pytest.warns(UserWarning, match='Expected `ordered-dict.*` - serialized value may not be as expected'):
        output = s.to_python({'a': 1})
    assert output == {'a': 1}
    assert type(output) is dict
    with pytest.warns(UserWarning, match='Expected `ordered-dict.*` - serialized value may not be as expected'):
        assert s.to_json({'a': 1}) == b'{"a":1}'


def test_ordered_dict_infer() -> None:
    # serialization of an `OrderedDict` under an `any` schema uses type inference:
    s = SchemaSerializer(cs.any_schema())
    output = s.to_python(OrderedDict({'a': OrderedDict({'b': 1})}))
    assert output == OrderedDict({'a': OrderedDict({'b': 1})})
    assert type(output) is OrderedDict
    assert type(output['a']) is OrderedDict
    assert s.to_python(OrderedDict({'a': 1}), mode='json') == {'a': 1}
    assert type(s.to_python(OrderedDict({'a': 1}), mode='json')) is dict
    assert s.to_json(OrderedDict({'a': 1})) == b'{"a":1}'
    assert json.loads(s.to_json(OrderedDict({'a': OrderedDict({'b': 1})}))) == {'a': {'b': 1}}


def test_ordered_dict_from_dict_serializer() -> None:
    # a `dict` schema still accepts an `OrderedDict` (as a `dict` subclass):
    s = SchemaSerializer(cs.dict_schema(cs.str_schema(), cs.int_schema()))
    output = s.to_python(OrderedDict({'a': 1}))
    assert output == {'a': 1}
    assert type(output) is dict
