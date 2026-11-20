"""Dictionary cursor parity and native error coverage."""

from typing import Annotated

import pytest
from pydantic_core import PydanticOmit, SchemaValidator, ValidationError, core_schema

from pydantic import AfterValidator, TypeAdapter


def omit_zero(value: int) -> int:
    if value == 0:
        raise PydanticOmit
    return value


@pytest.mark.parametrize(
    'data, expected',
    [
        ('{"a":1,"a":0}', {'a': 1}),
        ('{"a":1,"b":2,"a":0}', {'a': 1, 'b': 2}),
        ('{"a":1,"\\u0061":0}', {'a': 1}),
        ('{"a":0,"a":2}', {'a': 2}),
        ('{"a":1,"a":2,"b":0,"c":3}', {'a': 2, 'c': 3}),
    ],
)
def test_cursor_dict_omitted_duplicates(data: str, expected: dict[str, int]) -> None:
    adapter = TypeAdapter(dict[str, Annotated[int, AfterValidator(omit_zero)]])
    # A chain disables the root cursor while preserving JSON input semantics.
    # A before callback would materialize a Python dict and deduplicate raw keys.
    ordinary = SchemaValidator(core_schema.chain_schema([adapter.core_schema, core_schema.any_schema()]))
    assert ordinary.validate_json(data) == expected
    assert adapter.validate_json(data) == expected


@pytest.mark.parametrize('data, expected', [('{"1":1,"01":0}', {1: 1}), ('{"1":1,"1":0}', {1: 1})])
def test_cursor_dict_omission_keeps_distinct_raw_keys(data: str, expected: dict[int, int]) -> None:
    adapter = TypeAdapter(dict[int, Annotated[int, AfterValidator(omit_zero)]])
    assert adapter.validate_json(data) == expected


@pytest.mark.parametrize('fail_fast', [False, True])
@pytest.mark.parametrize(
    'data',
    [
        '{"1":1,"bad":"bad","2":"bad","3":4}',
        '{"1":"bad","bad":"bad","3":4}',
        '{"1":"bad","1":2}',
        '{"1":1,"2":["bad",3],"3":"bad"}',
        '{"1":1,"\\u0032":"bad"}',
    ],
)
def test_cursor_dict_error_policy_matches_ordinary_json(data: str, fail_fast: bool) -> None:
    schema = core_schema.dict_schema(core_schema.int_schema(), core_schema.int_schema(), fail_fast=fail_fast)
    ordinary = SchemaValidator(core_schema.chain_schema([schema, core_schema.any_schema()]))
    with pytest.raises(ValidationError) as expected:
        ordinary.validate_json(data)
    with pytest.raises(ValidationError) as actual:
        SchemaValidator(schema).validate_json(data)
    assert actual.value.errors(include_url=False) == expected.value.errors(include_url=False)


@pytest.mark.parametrize('fail_fast', [False, True])
def test_cursor_dict_errors_do_not_replay_successful_values(fail_fast: bool) -> None:
    calls: list[int] = []

    def record(value: int) -> int:
        calls.append(value)
        return value

    schema = core_schema.dict_schema(
        core_schema.str_schema(),
        core_schema.no_info_after_validator_function(record, core_schema.int_schema()),
        fail_fast=fail_fast,
    )
    with pytest.raises(ValidationError) as actual:
        SchemaValidator(schema).validate_json('{"a":1,"b":"bad","c":3}')
    assert [error['loc'] for error in actual.value.errors()] == [('b',)]
    assert calls == ([1] if fail_fast else [1, 3])


@pytest.mark.parametrize('maximum, minimum, expected_calls', [(1, None, [1, 2]), (None, 4, [1, 2, 3])])
def test_cursor_dict_bounds_do_not_replay(maximum: int | None, minimum: int | None, expected_calls: list[int]) -> None:
    calls: list[int] = []

    def record(value: int) -> int:
        calls.append(value)
        return value

    schema = core_schema.dict_schema(
        core_schema.str_schema(),
        core_schema.no_info_after_validator_function(record, core_schema.int_schema()),
        max_length=maximum,
        min_length=minimum,
    )
    data = '{"a":1,"b":2,"c":3}'
    ordinary = SchemaValidator(core_schema.chain_schema([schema, core_schema.any_schema()]))
    with pytest.raises(ValidationError) as expected:
        ordinary.validate_json(data)
    calls.clear()
    with pytest.raises(ValidationError) as actual:
        SchemaValidator(schema).validate_json(data)
    assert actual.value.errors(include_url=False) == expected.value.errors(include_url=False)
    assert calls == expected_calls


@pytest.mark.parametrize('data', [b'{"a":"bad","b":}', b'{"a":"bad","b":"\xff"}', b'{"a":"bad"} trailing'])
def test_cursor_dict_fail_fast_preserves_json_syntax_priority(data: bytes) -> None:
    schema = core_schema.dict_schema(core_schema.str_schema(), core_schema.int_schema(), fail_fast=True)
    with pytest.raises(ValidationError) as actual:
        SchemaValidator(schema).validate_json(data)
    assert actual.value.errors()[0]['type'] == 'json_invalid'


@pytest.mark.parametrize('data', [b'{"a":1,"b":2,"c":}', b'{"a":1,"b":2,"c":"\xff"}'])
def test_cursor_dict_maximum_preserves_json_syntax_priority(data: bytes) -> None:
    schema = core_schema.dict_schema(core_schema.str_schema(), core_schema.int_schema(), max_length=1)
    with pytest.raises(ValidationError) as actual:
        SchemaValidator(schema).validate_json(data)
    assert actual.value.errors()[0]['type'] == 'json_invalid'
