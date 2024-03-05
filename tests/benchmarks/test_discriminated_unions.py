from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter


def test_schema_build() -> None:
    class NestedState(BaseModel):
        state_type: Literal['nested']
        substate: AnyState

    class LoopState(BaseModel):
        state_type: Literal['loop']
        substate: AnyState

    class LeafState(BaseModel):
        state_type: Literal['leaf']

    AnyState = Annotated[NestedState | LoopState | LeafState, Field(..., discriminator='state_type')]
    adapter = TypeAdapter(AnyState)
    assert adapter.core_schema['schema']['type'] == 'tagged-union'


def test_efficiency_with_highly_nested_examples() -> None:
    def build_nested_state(n):
        if n <= 0:
            return {'state_type': 'leaf'}
        else:
            return {'state_type': 'loop', 'substate': {'state_type': 'nested', 'substate': build_nested_state(n - 1)}}

    class NestedState(BaseModel):
        state_type: Literal['nested']
        substate: AnyState

    class LoopState(BaseModel):
        state_type: Literal['loop']
        substate: AnyState

    class LeafState(BaseModel):
        state_type: Literal['leaf']

    AnyState = Annotated[NestedState | LoopState | LeafState, Field(..., discriminator='state_type')]
    adapter = TypeAdapter(AnyState)

    for i in range(10, 100):
        very_nested_input = build_nested_state(i)
        adapter.validate_python(very_nested_input)
