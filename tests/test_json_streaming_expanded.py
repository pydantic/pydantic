"""Coverage for the expanded optional JSON cursor plan."""

from datetime import UTC
from typing import Any

import pytest

from pydantic import BaseModel, TypeAdapter, ValidationError


def test_expanded_streaming_nested_models_in_root_list() -> None:
    """https://github.com/pydantic/pydantic/pull/14123"""

    class Leaf(BaseModel):
        value: int

    class Middle(BaseModel):
        leaves: list[Leaf]
        mapped: dict[str, list[Leaf]]

    class Root(BaseModel):
        middle: Middle

    adapter = TypeAdapter(list[Root])
    assert not adapter.validator._stream_plan_accepted
    assert adapter.validator._expanded_stream_plan_accepted
    result = adapter.validate_json('[{"middle":{"leaves":[{"value":"1"}],"mapped":{"x":[{"value":2}]}}}]')
    assert isinstance(result[0].middle, Middle)
    assert isinstance(result[0].middle.leaves[0], Leaf)
    assert result[0].model_dump() == {'middle': {'leaves': [{'value': 1}], 'mapped': {'x': [{'value': 2}]}}}
    assert result[0].middle.model_fields_set == {'leaves', 'mapped'}
    with pytest.raises(
        ValidationError, check=lambda error: error.errors()[0]['loc'] == (0, 'middle', 'leaves', 0, 'value')
    ):
        adapter.validate_json('[{"middle":{"leaves":[{"value":"bad"}],"mapped":{}}}]')


def test_expanded_streaming_constant_defaults_and_local_scalars() -> None:
    """https://github.com/pydantic/pydantic/pull/14123"""
    from datetime import datetime
    from decimal import Decimal
    from typing import Literal
    from uuid import UUID

    from pydantic import Field

    class Child(BaseModel):
        value: int

    class Model(BaseModel):
        kind: Literal['record'] = 'record'
        count: int = Field(default='4', validate_default=True)
        tags: list[str] = []
        child: Child = Child(value=5)
        positive: int = Field(gt=0)
        timestamp: datetime
        amount: Decimal
        identifier: UUID

    assert not Model.__pydantic_validator__._stream_plan_accepted
    assert Model.__pydantic_validator__._expanded_stream_plan_accepted
    data = '{"positive":2,"timestamp":"2026-11-19T00:00:00Z","amount":"1.25","identifier":"12345678-1234-5678-1234-567812345678"}'
    result = Model.model_validate_json(data)
    other = Model.model_validate_json(data)
    assert result.kind == 'record'
    assert result.count == 4
    assert result.child.value == 5
    assert isinstance(result.child, Child)
    assert result.timestamp == datetime(2026, 11, 19, tzinfo=UTC)
    assert result.amount == Decimal('1.25')
    assert result.identifier == UUID('12345678-1234-5678-1234-567812345678')
    assert result.model_fields_set == {'positive', 'timestamp', 'amount', 'identifier'}
    result.tags.append('changed')
    assert other.tags == []
    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['loc'] == ('positive',)):
        Model.model_validate_json(data.replace('"positive":2', '"positive":0'))


@pytest.mark.parametrize(
    ('annotation', 'document', 'expected'),
    [
        (int, '123', 123),
        (int, '1234567890123456789012345678901234567890', 1234567890123456789012345678901234567890),
        (float, '1.25', 1.25),
        (str, '"hello"', 'hello'),
        (bool, 'true', True),
        (type(None), 'null', None),
        (list[int], '[1,"2",3]', [1, 2, 3]),
        (list[float | None], '[1,null,2.5]', [1.0, None, 2.5]),
        (dict[str, list[int]], '{"x":[1,"2"],"x":[3]}', {'x': [3]}),
    ],
)
def test_expanded_streaming_scalar_and_container_roots(annotation: Any, document: str, expected: Any) -> None:
    """https://github.com/pydantic/pydantic/pull/14123"""
    adapter = TypeAdapter(annotation)
    assert not adapter.validator._stream_plan_accepted
    assert adapter.validator._expanded_stream_plan_accepted
    assert adapter.validate_json(document) == expected


def test_expanded_streaming_root_dictionary_constructs_models() -> None:
    """https://github.com/pydantic/pydantic/pull/14123"""
    from typing import Annotated

    from pydantic import Field

    class Model(BaseModel):
        value: int

    adapter = TypeAdapter(Annotated[dict[str, Model], Field(min_length=1, max_length=2)])
    assert not adapter.validator._stream_plan_accepted
    assert adapter.validator._expanded_stream_plan_accepted
    result = adapter.validate_json('{"a":{"value":1},"b":{"value":"2"}}')
    assert all(isinstance(value, Model) for value in result.values())
    assert {key: value.model_dump() for key, value in result.items()} == {'a': {'value': 1}, 'b': {'value': 2}}
    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['loc'] == ('a', 'value')):
        adapter.validate_json('{"a":{"value":"invalid"}}')
    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['type'] == 'too_short'):
        adapter.validate_json('{}')


def test_expanded_streaming_plan_budget_handles_reused_model_dag() -> None:
    """https://github.com/pydantic/pydantic/pull/14123"""
    from pydantic import create_model

    model: type[BaseModel] = create_model('BudgetLeaf', value=(int, ...))
    for depth in range(6):
        child = model
        model = create_model(f'BudgetLevel{depth}', **{f'item{i}': (child, ...) for i in range(5)})
        if depth == 2:
            assert model.__pydantic_validator__._expanded_stream_plan_accepted
    assert not model.__pydantic_validator__._expanded_stream_plan_accepted
    with pytest.raises(ValidationError, check=lambda error: len(error.errors()) == 5):
        model.model_validate_json('{}')
