from __future__ import annotations

from typing import Literal, Union

import pytest
from typing_extensions import Annotated

from pydantic import BaseModel, Field, TypeAdapter


class NestedState(BaseModel):
    state_type: Literal['nested']
    substate: AnyState


class LoopState(BaseModel):
    state_type: Literal['loop']
    substate: AnyState


class LeafState(BaseModel):
    state_type: Literal['leaf']


AnyState = Annotated[Union[NestedState, LoopState, LeafState], Field(..., discriminator='state_type')]


@pytest.mark.benchmark
def test_schema_build() -> None:
    adapter = TypeAdapter(AnyState)
    assert adapter.core_schema['schema']['type'] == 'tagged-union'


any_state_adapter = TypeAdapter(AnyState)


def build_nested_state(n):
    if n <= 0:
        return {'state_type': 'leaf'}
    else:
        return {'state_type': 'loop', 'substate': {'state_type': 'nested', 'substate': build_nested_state(n - 1)}}


@pytest.mark.benchmark
def test_efficiency_with_highly_nested_examples() -> None:
    # can go much higher, but we keep it reasonably low here for a proof of concept
    for i in range(1, 12):
        very_nested_input = build_nested_state(i)
        any_state_adapter.validate_python(very_nested_input)
