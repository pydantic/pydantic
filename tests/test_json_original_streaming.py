import copy
import json
import math
import sys
from types import FrameType
from typing import Annotated, Any

import pytest

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, ValidationInfo, field_validator


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


@pytest.mark.parametrize(
    ('annotation', 'data', 'expected'),
    [
        (list[int], '[1,"2",3.0,true,1000000000000000000000000000000]', [1, 2, 3, 1, 10**30]),
        (dict[str, int], '{"a":1,"b":"2","c":1000000000000000000000000000000}', {'a': 1, 'b': 2, 'c': 10**30}),
        (list[bool], '[0,1,"true","false"]', [False, True, True, False]),
        (list[float], '[1,"2.5",3.0]', [1.0, 2.5, 3.0]),
        (list[str], '["a",1,2.5]', ['a', '1', '2.5']),
    ],
)
def test_streamed_native_coercions_preserve_values(annotation: Any, data: str, expected: object) -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""
    adapter = TypeAdapter(annotation, config=ConfigDict(coerce_numbers_to_str=True))
    assert adapter.validate_json(data) == expected


def test_streamed_native_coercion_obeys_strict_override() -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""
    adapter = TypeAdapter(list[int], config=ConfigDict(strict=True))
    with pytest.raises(ValidationError):
        adapter.validate_json('[1,"2"]')
    assert adapter.validate_json('[1,"2"]', strict=False) == [1, 2]
    assert adapter.validate_json('[1000000000000000000000000000000]', strict=True) == [10**30]


@pytest.mark.parametrize('value', [2**63, -(2**63) - 1, 10**200, -(10**200)])
@pytest.mark.parametrize('strict', [False, True])
def test_streamed_bigints_keep_value_and_sign(value: int, strict: bool) -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""

    class Model(BaseModel):
        scalar: int
        values: list[int]
        mapping: dict[str, int]

    data = json.dumps({'scalar': value, 'values': [value], 'mapping': {'value': value}})
    result = Model.model_validate_json(data, strict=strict)
    assert result.scalar == value
    assert result.values == [value]
    assert result.mapping == {'value': value}
    assert TypeAdapter(list[int]).validate_json(json.dumps([value]), strict=strict) == [value]


@pytest.mark.parametrize(('token', 'sign'), [('-0', 1), ('-0.0', -1), ('0', 1), ('0.0', 1)])
def test_streamed_float_zero_sign(token: str, sign: int) -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""
    scalar = TypeAdapter(float).validate_json(token)
    item = TypeAdapter(list[float]).validate_json(f'[{token}]')[0]
    assert math.copysign(1, scalar) == sign
    assert math.copysign(1, item) == sign


def test_streamed_float_retains_json_integer_digit_limit() -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""
    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['type'] == 'json_invalid'):
        TypeAdapter(float).validate_json('1' + '0' * 4300)


@pytest.mark.parametrize('token', ['Infinity', 'NaN', '1e400'])
def test_streamed_float_retains_nonfinite_policy(token: str) -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""
    assert not math.isfinite(TypeAdapter(float).validate_json(token))
    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['type'] == 'finite_number'):
        TypeAdapter(float, config=ConfigDict(allow_inf_nan=False)).validate_json(token)
