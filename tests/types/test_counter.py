import collections
import typing
from collections import Counter
from typing import Annotated, Any

import pytest
import typing_extensions

from pydantic import BaseModel, Field, TypeAdapter, ValidationError


@pytest.mark.parametrize(
    'field_type',
    [
        pytest.param(typing.Counter, id='typing.Counter'),
        pytest.param(typing_extensions.Counter, id='typing_extensions.Counter'),
        pytest.param(collections.Counter, id='collections.Counter'),
    ],
)
def test_counter(field_type) -> None:
    ta = TypeAdapter(field_type)

    v = ta.validate_python(Counter({'a': 1, 'b': 2}))
    assert isinstance(v, Counter)
    assert v == Counter({'a': 1, 'b': 2})

    v = ta.validate_python({'a': '1', 'b': 2})
    assert isinstance(v, Counter)
    assert v == Counter({'a': 1, 'b': 2})

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python([1, 2, 3])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'counter_type', 'loc': (), 'msg': 'Input should be a valid Counter', 'input': [1, 2, 3]}
    ]

    assert ta.json_schema() == {'type': 'object', 'additionalProperties': {'type': 'integer'}}


@pytest.mark.parametrize(
    'field_type',
    [
        pytest.param(typing.Counter[str], id='typing.Counter'),
        pytest.param(typing_extensions.Counter[str], id='typing_extensions.Counter'),
        pytest.param(collections.Counter[str], id='collections.Counter'),
    ],
)
def test_counter_typed(field_type) -> None:
    ta = TypeAdapter(field_type)

    v = ta.validate_python({'a': 10})
    assert isinstance(v, Counter)
    assert v == Counter({'a': 10})

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({1: 1})
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'string_type', 'loc': (1, '[key]'), 'msg': 'Input should be a valid string', 'input': 1}
    ]

    assert ta.json_schema() == {'type': 'object', 'additionalProperties': {'type': 'integer'}}


def test_counter_value_validation() -> None:
    ta = TypeAdapter(Counter[str])

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({'a': 'a'})

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'a',
        }
    ]


def test_counter_values_preserved() -> None:
    ta = TypeAdapter(Counter[str])

    # zero and negative counts are kept as is (unlike `Counter.update()` which would sum them):
    v = ta.validate_python(Counter({'a': 3, 'b': 0, 'c': -2}))
    assert dict(v) == {'a': 3, 'b': 0, 'c': -2}
    assert dict(ta.dump_python(v)) == {'a': 3, 'b': 0, 'c': -2}
    assert ta.dump_json(v) == b'{"a":3,"b":0,"c":-2}'


def test_counter_json() -> None:
    ta = TypeAdapter(Counter[str])

    result = ta.validate_json('{"a": 1, "b": 2}')
    assert result == Counter({'a': 1, 'b': 2})
    assert isinstance(result, Counter)

    assert ta.dump_json(result) == b'{"a":1,"b":2}'


def test_counter_strict() -> None:
    ta = TypeAdapter(Counter[str], config={'strict': True})

    result = ta.validate_python(Counter({'a': 1}))
    assert result == Counter({'a': 1})

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({'a': 1})
    assert exc_info.value.errors()[0]['type'] == 'counter_type'

    # a JSON object is the only way to create a Counter from JSON, so it is allowed in strict mode:
    assert ta.validate_json('{"a": 1}') == Counter({'a': 1})


def test_constrained_counter() -> None:
    ta = TypeAdapter(Annotated[Counter[str], Field(min_length=1, max_length=2)])

    assert ta.validate_python({'a': 1}) == Counter({'a': 1})

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({})
    assert exc_info.value.errors()[0]['type'] == 'too_short'

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({'a': 1, 'b': 2, 'c': 3})
    assert exc_info.value.errors()[0]['type'] == 'too_long'


def test_counter_field() -> None:
    class Model(BaseModel):
        x: Counter[str]
        y: Counter = Counter()

    m = Model(x={'a': '1'})
    assert m.x == Counter({'a': 1})
    assert isinstance(m.x, Counter)
    assert m.y == Counter()

    assert m.model_dump() == {'x': Counter({'a': 1}), 'y': Counter()}
    assert isinstance(m.model_dump()['x'], Counter)
    assert m.model_dump(mode='json') == {'x': {'a': 1}, 'y': {}}
    assert type(m.model_dump(mode='json')['x']) is dict
    assert m.model_dump_json() == '{"x":{"a":1},"y":{}}'


def test_counter_nested() -> None:
    ta = TypeAdapter(dict[str, Counter[str]])

    result = ta.validate_python({'a': {'b': '1'}})
    assert result == {'a': Counter({'b': 1})}
    assert isinstance(result['a'], Counter)


def test_counter_json_schema() -> None:
    ta = TypeAdapter(Annotated[Counter[str], Field(min_length=1, max_length=2)])
    assert ta.json_schema() == {
        'type': 'object',
        'additionalProperties': {'type': 'integer'},
        'minProperties': 1,
        'maxProperties': 2,
    }


def test_counter_serialization_any() -> None:
    ta = TypeAdapter(Any)

    result = ta.dump_python(Counter({'a': 1}))
    assert result == Counter({'a': 1})
    assert isinstance(result, Counter)

    assert ta.dump_python(Counter({'a': 1}), mode='json') == {'a': 1}
    assert ta.dump_json(Counter({'a': 1})) == b'{"a":1}'
