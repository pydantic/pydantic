"""Dictionary cursor parity and native error coverage."""

from typing import Annotated

import pytest
from pydantic_core import PydanticOmit, SchemaValidator, core_schema

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
