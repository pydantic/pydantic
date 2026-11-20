"""Native errors from completely traversed JSON containers."""

from typing import Annotated

import pytest

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    Field,
    TypeAdapter,
    ValidationError,
    field_validator,
)


def test_cursor_model_list_errors_do_not_replay_fields() -> None:
    calls: list[int] = []

    def record(value: int) -> int:
        calls.append(value)
        return value

    class Model(BaseModel):
        values: list[Annotated[int, AfterValidator(record)]]
        other: int

    data = '{"values":[1,"bad",3],"other":"bad"}'
    with pytest.raises(ValidationError) as actual:
        Model.model_validate_json(data)
    assert [error['loc'] for error in actual.value.errors()] == [('values', 1), ('other',)]
    assert calls == [1, 3]


def test_cursor_model_missing_and_rejected_defaults_do_not_replay() -> None:
    calls: list[int] = []

    def reject(value: int) -> int:
        calls.append(value)
        raise ValueError('rejected default')

    class Model(BaseModel):
        missing: int
        default: Annotated[int, AfterValidator(reject)] = Field(default=1, validate_default=True)

    with pytest.raises(ValidationError) as actual:
        Model.model_validate_json('{}')
    assert [error['loc'] for error in actual.value.errors()] == [('missing',), ('default',)]
    assert calls == [1]


def test_cursor_model_errors_inside_list_do_not_replay() -> None:
    calls: list[int] = []

    class Model(BaseModel):
        value: int

        @field_validator('value')
        @classmethod
        def reject(cls, value: int) -> int:
            calls.append(value)
            raise ValueError('rejected')

    with pytest.raises(ValidationError) as actual:
        TypeAdapter(list[Model]).validate_json('[{"value":1},{"value":2}]')
    assert [error['loc'] for error in actual.value.errors()] == [(0, 'value'), (1, 'value')]
    assert calls == [1, 2]


@pytest.mark.parametrize(
    'data',
    [
        '{"values":["bad",2],"other":0}',
        '{"other":"bad","values":[1,"bad"]}',
        '{"values":[1]}',
        '{"other":0}',
        '{"ignored":[1,2],"values":["bad"],"other":0}',
    ],
)
def test_cursor_model_errors_match_ordinary(data: str) -> None:
    class Model(BaseModel):
        values: list[int]
        other: int = Field(gt=0)

    ordinary = TypeAdapter(Annotated[Model, BeforeValidator(lambda value: value)])
    with pytest.raises(ValidationError) as expected:
        ordinary.validate_json(data)
    with pytest.raises(ValidationError) as actual:
        Model.model_validate_json(data)
    assert actual.value.json(include_url=False) == expected.value.json(include_url=False)


@pytest.mark.parametrize(
    'data',
    [
        b'{"values":["bad",2],"other":1} trailing',
        b'{"values":["bad",2],"other":}',
        b'{"values":["bad",2],"ignored":"\xff"}',
        b'{"values":["bad",2]',
    ],
)
def test_cursor_model_errors_do_not_hide_invalid_json(data: bytes) -> None:
    class Model(BaseModel):
        values: Annotated[list[int], Field(fail_fast=True)]
        other: int

    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['type'] == 'json_invalid'):
        Model.model_validate_json(data)


def test_cursor_model_incomplete_child_keeps_sibling_locations() -> None:
    class Model(BaseModel):
        values: Annotated[list[int], Field(fail_fast=True)]
        other: int

    data = '{"values":["bad",2,3],"other":"bad"}'
    ordinary = TypeAdapter(Annotated[Model, BeforeValidator(lambda value: value)])
    with pytest.raises(ValidationError) as expected:
        ordinary.validate_json(data)
    with pytest.raises(ValidationError) as actual:
        Model.model_validate_json(data)
    assert actual.value.json(include_url=False) == expected.value.json(include_url=False)
