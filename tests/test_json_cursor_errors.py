"""Completed cursor lists use ordinary collection errors without document replay."""

from typing import Annotated, Any

import pytest
from pydantic_core import PydanticOmit

from pydantic import AfterValidator, BeforeValidator, Field, TypeAdapter, ValidationError


def test_cursor_list_errors_do_not_replay_callbacks() -> None:
    calls: list[int] = []

    def reject_three(value: int) -> int:
        calls.append(value)
        if value == 3:
            raise ValueError('three is forbidden')
        return value

    item = Annotated[int, AfterValidator(reject_three)]
    ordinary = TypeAdapter(Annotated[list[item], BeforeValidator(lambda value: value)])
    with pytest.raises(ValidationError) as expected:
        ordinary.validate_json('[1,3,5]')
    calls.clear()
    with pytest.raises(ValidationError) as actual:
        TypeAdapter(list[item]).validate_json('[1,3,5]')
    assert actual.value.json(include_url=False) == expected.value.json(include_url=False)
    assert calls == [1, 3, 5]


@pytest.mark.parametrize(
    'annotation,data',
    [
        (list[int], '["bad",1,null,1.5]'),
        (list[list[int]], '[["bad",2],[3,"bad"]]'),
        (list[Annotated[int, Field(gt=0)]], '[0,1,-1]'),
        (list[int | float], '[{},null,1]'),
        (list[dict[int, int]], '[{"bad":1,"2":"bad"},{"3":"bad"}]'),
        (Annotated[list[int], Field(fail_fast=True)], '["bad",null]'),
        (list[Annotated[list[int], Field(fail_fast=True)]], '[["bad",2,3],["bad"]]'),
        (Annotated[list[int], Field(max_length=1)], '["bad",2,3]'),
        (Annotated[list[int], Field(min_length=3)], '["bad",2]'),
    ],
)
def test_cursor_list_errors_match_ordinary_validation(annotation: Any, data: str) -> None:
    ordinary = TypeAdapter(Annotated[annotation, BeforeValidator(lambda value: value)])
    with pytest.raises(ValidationError) as expected:
        ordinary.validate_json(data)
    with pytest.raises(ValidationError) as actual:
        TypeAdapter(annotation).validate_json(data)
    assert actual.value.json(include_url=False) == expected.value.json(include_url=False)


@pytest.mark.parametrize(
    'data',
    [b'["bad",1] trailing', b'["bad",]', b'["bad","\xff"]', b'[["bad",2,3]'],
)
def test_cursor_list_errors_do_not_hide_invalid_json(data: bytes) -> None:
    annotation = list[Annotated[list[int], Field(fail_fast=True)]] if data.startswith(b'[[') else list[int]
    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['type'] == 'json_invalid'):
        TypeAdapter(annotation).validate_json(data)


def test_cursor_nested_list_errors_keep_locations_without_replay() -> None:
    calls: list[int] = []

    def reject_three(value: int) -> int:
        calls.append(value)
        if value == 3:
            raise ValueError('three is forbidden')
        return value

    adapter = TypeAdapter(list[list[Annotated[int, AfterValidator(reject_three)]]])
    with pytest.raises(ValidationError) as actual:
        adapter.validate_json('[[3,1],[1,3]]')
    assert [error['loc'] for error in actual.value.errors()] == [(0, 0), (1, 1)]
    assert calls == [3, 1, 1, 3]


def test_cursor_list_errors_preserve_omission_and_original_indices() -> None:
    calls: list[int] = []

    def omit_or_reject(value: int) -> int:
        calls.append(value)
        if value == 0:
            raise PydanticOmit
        if value < 0:
            raise ValueError('negative')
        return value

    adapter = TypeAdapter(list[Annotated[int, AfterValidator(omit_or_reject)]])
    with pytest.raises(ValidationError) as actual:
        adapter.validate_json('[0,1,-1,0,-2]')
    assert [error['loc'] for error in actual.value.errors()] == [(2,), (4,)]
    assert calls == [0, 1, -1, 0, -2]
