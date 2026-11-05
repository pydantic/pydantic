import collections
import typing
from collections import OrderedDict
from typing import Annotated, Any

import pytest
import typing_extensions

from pydantic import BaseModel, Field, TypeAdapter, ValidationError


def test_ordered_dict() -> None:
    ta = TypeAdapter(OrderedDict)

    assert ta.validate_python(OrderedDict([(1, 10), (2, 20)])) == OrderedDict([(1, 10), (2, 20)])
    assert ta.validate_python({1: 10, 2: 20}) == OrderedDict([(1, 10), (2, 20)])

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python([1, 2, 3])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'ordered_dict_type', 'loc': (), 'msg': 'Input should be a valid OrderedDict', 'input': [1, 2, 3]}
    ]


@pytest.mark.parametrize(
    'field_type',
    [
        pytest.param(typing.OrderedDict, id='typing.OrderedDict'),
        pytest.param(typing_extensions.OrderedDict, id='typing_extensions.OrderedDict'),
        pytest.param(collections.OrderedDict, id='collections.OrderedDict'),
    ],
)
def test_ordered_dict_from_ordered_dict(field_type) -> None:
    ta = TypeAdapter(field_type)

    od_value = collections.OrderedDict([('a', 1), ('b', 2)])

    v = ta.validate_python(od_value)

    assert isinstance(v, collections.OrderedDict)
    assert v == od_value
    # we don't make any promises about preserving instances
    # at the moment we always copy them for consistency and predictability
    # so this is more so documenting the current behavior than a promise
    # we make to users
    assert v is not od_value

    assert ta.json_schema() == {'type': 'object', 'additionalProperties': True}


@pytest.mark.parametrize(
    'field_type',
    [
        pytest.param(typing.OrderedDict[str, int], id='typing.OrderedDict'),
        pytest.param(typing_extensions.OrderedDict[str, int], id='typing_extensions.OrderedDict'),
        pytest.param(collections.OrderedDict[str, int], id='collections.OrderedDict'),
    ],
)
def test_ordered_dict_from_ordered_dict_typed(field_type) -> None:
    ta = TypeAdapter(field_type)

    od_value = collections.OrderedDict([('a', 1), ('b', 2)])

    v = ta.validate_python(od_value)

    assert isinstance(v, collections.OrderedDict)
    assert v == od_value

    assert ta.json_schema() == {
        'type': 'object',
        'additionalProperties': {'type': 'integer'},
    }


@pytest.mark.parametrize(
    'field_type',
    [
        pytest.param(typing.OrderedDict, id='typing.OrderedDict'),
        pytest.param(collections.OrderedDict, id='collections.OrderedDict'),
    ],
)
def test_ordered_dict_from_dict(field_type) -> None:
    ta = TypeAdapter(field_type)

    od_value = {'a': 1, 'b': 2}

    v = ta.validate_python(od_value)

    assert isinstance(v, collections.OrderedDict)
    assert v == collections.OrderedDict(od_value)


def test_ordered_dict_order_preserved() -> None:
    ta = TypeAdapter(OrderedDict[str, int])

    od_value = OrderedDict([('a', 1), ('b', 2), ('c', 3)])
    od_value.move_to_end('a')

    v = ta.validate_python(od_value)
    assert list(v.items()) == [('b', 2), ('c', 3), ('a', 1)]
    assert list(ta.dump_python(v).items()) == [('b', 2), ('c', 3), ('a', 1)]
    assert ta.dump_json(v) == b'{"b":2,"c":3,"a":1}'


def test_ordered_dict_json() -> None:
    ta = TypeAdapter(OrderedDict[str, int])

    result = ta.validate_json('{"a": 1, "b": 2}')
    assert result == OrderedDict({'a': 1, 'b': 2})
    assert isinstance(result, OrderedDict)

    assert ta.dump_json(result) == b'{"a":1,"b":2}'


def test_ordered_dict_strict() -> None:
    ta = TypeAdapter(OrderedDict[str, int], config={'strict': True})

    result = ta.validate_python(OrderedDict({'a': 1}))
    assert result == OrderedDict({'a': 1})

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({'a': 1})
    assert exc_info.value.errors()[0]['type'] == 'ordered_dict_type'

    # a JSON object is the only way to create an OrderedDict from JSON, so it is allowed in strict mode:
    assert ta.validate_json('{"a": 1}') == OrderedDict({'a': 1})


def test_constrained_ordered_dict() -> None:
    ta = TypeAdapter(Annotated[OrderedDict[str, int], Field(min_length=1, max_length=2)])

    assert ta.validate_python({'a': 1}) == OrderedDict({'a': 1})

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({})
    assert exc_info.value.errors()[0]['type'] == 'too_short'

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({'a': 1, 'b': 2, 'c': 3})
    assert exc_info.value.errors()[0]['type'] == 'too_long'


def test_ordered_dict_field() -> None:
    class Model(BaseModel):
        x: OrderedDict[str, int]
        y: OrderedDict = OrderedDict()

    m = Model(x={'a': '1'})
    assert m.x == OrderedDict({'a': 1})
    assert isinstance(m.x, OrderedDict)
    assert m.y == OrderedDict()

    assert m.model_dump() == {'x': OrderedDict({'a': 1}), 'y': OrderedDict()}
    assert isinstance(m.model_dump()['x'], OrderedDict)
    assert m.model_dump(mode='json') == {'x': {'a': 1}, 'y': {}}
    assert type(m.model_dump(mode='json')['x']) is dict
    assert m.model_dump_json() == '{"x":{"a":1},"y":{}}'


def test_ordered_dict_nested() -> None:
    ta = TypeAdapter(OrderedDict[str, OrderedDict[str, int]])

    result = ta.validate_python({'a': {'b': '1'}})
    assert result == OrderedDict({'a': OrderedDict({'b': 1})})
    assert isinstance(result['a'], OrderedDict)


def test_ordered_dict_json_schema() -> None:
    """https://github.com/pydantic/pydantic/issues/13704"""
    ta = TypeAdapter(Annotated[OrderedDict[str, int], Field(min_length=1, max_length=2)])
    assert ta.json_schema() == {
        'type': 'object',
        'additionalProperties': {'type': 'integer'},
        'minProperties': 1,
        'maxProperties': 2,
    }


def test_ordered_dict_serialization_any() -> None:
    ta = TypeAdapter(Any)

    result = ta.dump_python(OrderedDict({'a': 1}))
    assert result == OrderedDict({'a': 1})
    assert isinstance(result, OrderedDict)

    assert ta.dump_python(OrderedDict({'a': 1}), mode='json') == {'a': 1}
    assert ta.dump_json(OrderedDict({'a': 1})) == b'{"a":1}'
