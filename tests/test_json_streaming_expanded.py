"""Coverage for the expanded optional JSON cursor plan."""

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
