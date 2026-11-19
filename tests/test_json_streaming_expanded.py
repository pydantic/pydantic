"""Coverage for the expanded optional JSON cursor plan."""

from datetime import UTC

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
