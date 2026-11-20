"""Union selection and errors on cursor-backed container values."""

from typing import Annotated, Any, Literal

import pytest

from pydantic import BaseModel, BeforeValidator, Field, TypeAdapter, ValidationError


@pytest.mark.parametrize('strict', [False, True])
@pytest.mark.parametrize('data', ['[1,2]', '["1","2"]', '["x",1]', '[{},null]'])
def test_cursor_union_list_selection_and_errors(data: str, strict: bool) -> None:
    schema = list[int] | list[str]
    adapter = TypeAdapter(schema)
    ordinary = TypeAdapter(Annotated[schema, BeforeValidator(lambda value: value)])
    try:
        expected = ordinary.validate_json(data, strict=strict)
    except ValidationError as error:
        with pytest.raises(ValidationError) as actual:
            adapter.validate_json(data, strict=strict)
        assert actual.value.json(include_url=False) == error.json(include_url=False)
    else:
        actual = adapter.validate_json(data, strict=strict)
        assert actual == expected
        assert [type(item) for item in actual] == [type(item) for item in expected]


@pytest.mark.parametrize('mode', ['smart', 'left_to_right'])
@pytest.mark.parametrize('data', ['{"a":1}', '{"a":1,"b":2}', '{"a":"bad"}'])
def test_cursor_union_model_scoring(mode: str, data: str) -> None:
    class First(BaseModel):
        a: int

    class Second(BaseModel):
        a: int
        b: int = 0

    schema = Annotated[First | Second, Field(union_mode=mode)]
    adapter = TypeAdapter(schema)
    ordinary = TypeAdapter(Annotated[schema, BeforeValidator(lambda value: value)])
    try:
        expected = ordinary.validate_json(data)
    except ValidationError as error:
        with pytest.raises(ValidationError) as actual:
            adapter.validate_json(data)
        assert actual.value.json(include_url=False) == error.json(include_url=False)
    else:
        actual = adapter.validate_json(data)
        assert type(actual) is type(expected)
        assert actual.model_dump() == expected.model_dump()


@pytest.mark.parametrize(
    'first',
    [Annotated[list[int], Field(max_length=1)], Annotated[list[str], Field(fail_fast=True)]],
    ids=['max-length', 'fail-fast'],
)
def test_cursor_union_local_replay_preserves_next_value(first: Any) -> None:
    schema = list[first | list[int]]
    assert TypeAdapter(schema).validate_json('[[1,2,3],[4,5]]') == [[1, 2, 3], [4, 5]]


def test_cursor_union_best_match_survives_later_branch_failure() -> None:
    class First(BaseModel):
        a: int

    class Second(BaseModel):
        b: int

    class Outer(BaseModel):
        value: First | Second
        following: int

    result = Outer.model_validate_json('{"value":{"a":1},"following":42}')
    assert isinstance(result.value, First)
    assert result.value.a == 1
    assert result.following == 42


@pytest.mark.parametrize('data', ['[1,2] trailing', '[1,]', r'["\ud800"]'])
def test_cursor_union_malformed_json_retains_json_error(data: str) -> None:
    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['type'] == 'json_invalid'):
        TypeAdapter(list[int] | list[str]).validate_json(data)


@pytest.mark.parametrize('kind', ['first', 'invalid'])
def test_cursor_union_complete_model_errors_do_not_replay(kind: str) -> None:
    calls: list[str] = []

    def record(value: Any) -> Any:
        calls.append('values')
        return value

    class First(BaseModel):
        kind: Literal['first']
        values: Annotated[list[int], BeforeValidator(record)]

    class Second(BaseModel):
        kind: Literal['second']
        values: Annotated[list[int], BeforeValidator(record)]

    adapter = TypeAdapter(First | Second)
    data = f'{{"kind":"{kind}","values":[1]}}'
    if kind == 'invalid':
        with pytest.raises(ValidationError) as error:
            adapter.validate_json(data)
        assert [item['type'] for item in error.value.errors()] == ['literal_error', 'literal_error']
    else:
        assert isinstance(adapter.validate_json(data), First)
    # Each branch visits its field once, including a branch with a preceding error.
    assert calls == ['values', 'values']
