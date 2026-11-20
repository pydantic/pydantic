"""Native complete-array failures retain ordinary error policy and JSON priority."""

import json

import pytest
from pydantic_core import PydanticOmit, SchemaValidator, ValidationError, core_schema


@pytest.mark.parametrize(
    'maximum, minimum, fail_fast, items, expected_calls',
    [
        (2, None, False, [1, 2, 3, 4], [1, 2, 3]),
        (None, 5, False, [1, 2, 3], [1, 2, 3]),
        (None, None, True, [1, 'bad', 3], [1]),
        (1, None, True, [1, 'bad', 3], [1]),
        (None, 4, False, [1, 'bad'], [1]),
        (1, None, False, [0, 1, 2, 3], [0, 1, 2]),
    ],
)
def test_cursor_list_bound_and_fail_fast_errors_do_not_replay(
    maximum: int | None,
    minimum: int | None,
    fail_fast: bool,
    items: list[int | str],
    expected_calls: list[int],
) -> None:
    calls: list[int] = []

    def record(value: int) -> int:
        calls.append(value)
        if value == 0:
            raise PydanticOmit
        return value

    schema = core_schema.list_schema(
        core_schema.no_info_after_validator_function(record, core_schema.int_schema()),
        max_length=maximum,
        min_length=minimum,
        fail_fast=fail_fast,
    )
    ordinary = SchemaValidator(core_schema.chain_schema([schema, core_schema.any_schema()]))
    data = json.dumps(items)
    with pytest.raises(ValidationError) as expected:
        ordinary.validate_json(data)
    calls.clear()
    with pytest.raises(ValidationError) as actual:
        SchemaValidator(schema).validate_json(data)
    assert actual.value.errors(include_url=False) == expected.value.errors(include_url=False)
    assert calls == expected_calls


@pytest.mark.parametrize('maximum, minimum', [(1, None), (None, 4)])
def test_cursor_untyped_list_bounds_match_ordinary(maximum: int | None, minimum: int | None) -> None:
    schema = core_schema.list_schema(max_length=maximum, min_length=minimum)
    ordinary = SchemaValidator(core_schema.chain_schema([schema, core_schema.any_schema()]))
    data = '[1,{"a":2},3]'
    with pytest.raises(ValidationError) as expected:
        ordinary.validate_json(data)
    with pytest.raises(ValidationError) as actual:
        SchemaValidator(schema).validate_json(data)
    assert actual.value.errors(include_url=False) == expected.value.errors(include_url=False)


@pytest.mark.parametrize(
    'data, fail_fast, maximum',
    [
        (b'[1,"bad",{"missing":}]', True, None),
        (b'[1,"bad","\xff"]', True, None),
        (b'[1,2,{"missing":}]', False, 1),
        (b'[1,2,"\xff"]', False, 1),
        (b'[1,"bad",3] trailing', True, None),
    ],
)
def test_cursor_early_list_errors_preserve_json_syntax_priority(
    data: bytes, fail_fast: bool, maximum: int | None
) -> None:
    schema = core_schema.list_schema(core_schema.int_schema(), max_length=maximum, fail_fast=fail_fast)
    with pytest.raises(ValidationError) as actual:
        SchemaValidator(schema).validate_json(data)
    assert actual.value.errors()[0]['type'] == 'json_invalid'


def test_cursor_list_bound_errors_nested_in_dictionary_do_not_replay() -> None:
    calls: list[int] = []

    def record(value: int) -> int:
        calls.append(value)
        return value

    schema = core_schema.dict_schema(
        core_schema.str_schema(),
        core_schema.list_schema(
            core_schema.no_info_after_validator_function(record, core_schema.int_schema()), max_length=1
        ),
    )
    with pytest.raises(ValidationError) as actual:
        SchemaValidator(schema).validate_json('{"a":[1,2],"b":[3]}')
    assert [error['loc'] for error in actual.value.errors()] == [('a',)]
    assert calls == [1, 2, 3]
