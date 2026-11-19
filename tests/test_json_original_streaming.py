import copy
import sys
from types import FrameType
from typing import Annotated

import pytest

from pydantic import BaseModel, Field, TypeAdapter, ValidationError, ValidationInfo, field_validator


def test_streamed_valid_defaults_receive_field_context() -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""

    class Model(BaseModel):
        username: str = Field(default=' Alice ', validate_default=True)
        display_name: str = Field(default=' Alice ', validate_default=True)

        @field_validator('username', 'display_name')
        @classmethod
        def normalize(cls, value: str, info: ValidationInfo) -> str:
            value = value.strip()
            return value.lower() if info.field_name == 'username' else value

    assert Model.__pydantic_validator__._stream_plan_accepted
    assert Model.model_validate_json('{}').model_dump() == {'username': 'alice', 'display_name': 'Alice'}


def test_streamed_list_bound_limits_mutable_default_copies() -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""

    class Item(BaseModel):
        payload: list[int] = [0] * 1000

    adapter = TypeAdapter(Annotated[list[Item], Field(max_length=1)])
    data = '[' + ','.join(['{}'] * 1000) + ']'
    copies = 0
    deepcopy_code = copy.deepcopy.__code__

    def count_copies(frame: FrameType, event: str, _argument: object) -> None:
        nonlocal copies
        if event == 'call' and frame.f_code is deepcopy_code and isinstance(frame.f_locals.get('x'), list):
            copies += 1

    previous = sys.getprofile()
    sys.setprofile(count_copies)
    try:
        with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['type'] == 'too_long'):
            adapter.validate_json(data)
    finally:
        sys.setprofile(previous)
    # One speculative item, followed by the ordinary path's bounded validation.
    assert copies <= 3
