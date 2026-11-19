"""Regression coverage for direct JSON traversal on the validator graph."""

from typing import Annotated

import pytest

from pydantic import BaseModel, Field, TypeAdapter, ValidationError, ValidationInfo, field_validator


def test_cursor_mixed_model_defaults_and_field_order() -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""
    calls: list[tuple[str | None, list[int]]] = []

    class Model(BaseModel):
        numbers: list[int]
        username: str = Field(default=' Alice ', validate_default=True)

        @field_validator('username')
        @classmethod
        def normalize(cls, value: str, info: ValidationInfo) -> str:
            assert info.data is not None
            calls.append((info.field_name, info.data['numbers']))
            return value.strip().lower()

    result = Model.model_validate_json('{"username":" Alice ","numbers":[1,"2",3]}')
    assert result.model_dump() == {'numbers': [1, 2, 3], 'username': 'alice'}
    assert calls == [('username', [1, 2, 3])]
    calls.clear()
    assert Model.model_validate_json('{"numbers":[4]}').username == 'alice'
    assert calls == [('username', [4])]


@pytest.mark.parametrize('data', [b'[{"value":1}] trailing', b'[{"value":1}, {"value":}]'])
def test_cursor_syntax_checked_before_callbacks(data: bytes) -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""
    calls: list[int] = []

    class Model(BaseModel):
        value: int

        @field_validator('value')
        @classmethod
        def record(cls, value: int) -> int:
            calls.append(value)
            return value

    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['type'] == 'json_invalid'):
        TypeAdapter(list[Model]).validate_json(data)
    assert calls == []


def test_cursor_does_not_replay_rejected_callback() -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""
    calls: list[int] = []

    class Model(BaseModel):
        value: int

        @field_validator('value')
        @classmethod
        def reject(cls, value: int) -> int:
            calls.append(value)
            raise ValueError('rejected')

    with pytest.raises(ValidationError):
        Model.model_validate_json('{"value":1}')
    assert calls == [1]


def test_cursor_duplicate_fields_select_last_value_before_validation() -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""
    calls: list[int] = []

    class Model(BaseModel):
        value: int

        @field_validator('value')
        @classmethod
        def record(cls, value: int) -> int:
            calls.append(value)
            return value

    assert Model.model_validate_json('{"value":"invalid","value":2}').value == 2
    assert calls == [2]


def test_cursor_list_bounds_stop_default_construction() -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""
    calls: list[int] = []

    class Model(BaseModel):
        value: int = Field(default_factory=lambda: calls.append(1) or 1)

    adapter = TypeAdapter(Annotated[list[Model], Field(max_length=1)])
    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['ctx']['actual_length'] == 1000):
        adapter.validate_json('[' + ','.join('{}' for _ in range(1000)) + ']')
    assert calls == [1, 1]


def test_cursor_nested_missing_field_error_input() -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""

    class Model(BaseModel):
        value: int

    with pytest.raises(
        ValidationError,
        check=lambda error: (
            error.errors(include_url=False)
            == [{'type': 'missing', 'loc': (1, 'value'), 'msg': 'Field required', 'input': {}}]
        ),
    ):
        TypeAdapter(list[Model]).validate_json('[{"value":1},{}]')


def test_cursor_checks_ignored_utf8_and_depth() -> None:
    """https://github.com/pydantic/pydantic/pull/14123"""

    class Model(BaseModel):
        value: int

    for data in (b'{"value":1,"ignored":"\xff"}', b'{"value":1,"ignored":' + b'[' * 200 + b'1' + b']' * 200 + b'}'):
        with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['type'] == 'json_invalid'):
            Model.model_validate_json(data)


@pytest.mark.parametrize('max_length', [True, False])
def test_cursor_nested_list_early_errors_continue_outer_array(max_length: bool) -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""
    constraint = Field(max_length=1) if max_length else Field(fail_fast=True)
    adapter = TypeAdapter(list[Annotated[list[int], constraint]])
    with pytest.raises(ValidationError) as caught:
        adapter.validate_json('[["bad",2,3],["also bad"]]')
    assert [error['loc'] for error in caught.value.errors()] == ([(0,), (1, 0)] if max_length else [(0, 0), (1, 0)])
