"""Tests for the experimental transform module."""
from __future__ import annotations

from typing import Any

import pytest
from typing_extensions import Annotated

from pydantic import TypeAdapter, ValidationError
from pydantic.experimental.pipeline import parse


@pytest.mark.parametrize('potato_variation', ['potato', ' potato ', ' potato', 'potato ', ' POTATO ', ' PoTatO '])
def test_parse_str(potato_variation: str) -> None:
    ta_lower = TypeAdapter(Annotated[str, parse(str).str.strip().str.lower()])
    assert ta_lower.validate_python(potato_variation) == 'potato'


def test_parse_str_with_pattern() -> None:
    ta_pattern = TypeAdapter(Annotated[str, parse(str).str.pattern(r'[a-z]+')])
    assert ta_pattern.validate_python('potato') == 'potato'
    with pytest.raises(ValueError):
        ta_pattern.validate_python('POTATO')


@pytest.mark.parametrize(
    'method, method_arg, input_string, expected_output',
    [
        # transforms
        ('lower', None, 'POTATO', 'potato'),
        ('upper', None, 'potato', 'POTATO'),
        ('title', None, 'potato potato', 'Potato Potato'),
        ('strip', None, ' potato ', 'potato'),
        # constraints
        ('pattern', r'[a-z]+', 'potato', 'potato'),  # check lowercase
        # predicates
        ('contains', 'pot', 'potato', 'potato'),
        ('starts_with', 'pot', 'potato', 'potato'),
        ('ends_with', 'ato', 'potato', 'potato'),
    ],
)
def test_string_validator_valid(method: str, method_arg: str | None, input_string: str, expected_output: str):
    # annotated metadata is equivalent to parse(str).str.method(method_arg)
    # ex: parse(str).str.contains('pot')
    annotated_metadata = getattr(parse(str).str, method)
    annotated_metadata = annotated_metadata(method_arg) if method_arg else annotated_metadata()

    ta = TypeAdapter(Annotated[str, annotated_metadata])
    assert ta.validate_python(input_string) == expected_output


def test_string_validator_invalid() -> None:
    ta_contains = TypeAdapter(Annotated[str, parse(str).str.contains('potato')])
    with pytest.raises(ValidationError):
        ta_contains.validate_python('tomato')

    ta_starts_with = TypeAdapter(Annotated[str, parse(str).str.starts_with('potato')])
    with pytest.raises(ValidationError):
        ta_starts_with.validate_python('tomato')

    ta_ends_with = TypeAdapter(Annotated[str, parse(str).str.ends_with('potato')])
    with pytest.raises(ValidationError):
        ta_ends_with.validate_python('tomato')


def test_parse_int() -> None:
    ta_gt = TypeAdapter(Annotated[int, parse(int).gt(0)])
    assert ta_gt.validate_python(1) == 1
    assert ta_gt.validate_python('1') == 1
    with pytest.raises(ValidationError):
        ta_gt.validate_python(0)

    ta_gt_strict = TypeAdapter(Annotated[int, parse(int, strict=True).gt(0)])
    assert ta_gt_strict.validate_python(1) == 1
    with pytest.raises(ValidationError):
        ta_gt_strict.validate_python('1')
    with pytest.raises(ValidationError):
        ta_gt_strict.validate_python(0)


def test_parse_str_to_int() -> None:
    ta = TypeAdapter(Annotated[int, parse(str).str.strip().parse(int)])
    assert ta.validate_python('1') == 1
    assert ta.validate_python(' 1 ') == 1
    with pytest.raises(ValidationError):
        ta.validate_python('a')


def test_predicates() -> None:
    ta_int = TypeAdapter(Annotated[int, parse(int).predicate(lambda x: x % 2 == 0)])
    assert ta_int.validate_python(2) == 2
    with pytest.raises(ValidationError):
        ta_int.validate_python(1)

    ta_str = TypeAdapter(Annotated[str, parse(str).predicate(lambda x: x != 'potato')])
    assert ta_str.validate_python('tomato') == 'tomato'
    with pytest.raises(ValidationError):
        ta_str.validate_python('potato')


@pytest.mark.parametrize(
    'model, expected_val_schema, expected_ser_schema',
    [
        (
            Annotated[int | str, parse() | parse(str)],
            {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
            {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
        ),
        (
            Annotated[int, parse() | parse(str).parse(int)],
            {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
            {'type': 'integer'},
        ),
        (
            Annotated[int, parse() | parse(str).transform(int)],
            {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
            {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
        ),
        (
            Annotated[int, parse() | parse(str).transform(int).parse(int)],
            {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
            {'type': 'integer'},
        ),
        (
            Annotated[int, parse(int).gt(0).lt(100)],
            {'type': 'integer', 'exclusiveMinimum': 0, 'exclusiveMaximum': 100},
            {'type': 'integer', 'exclusiveMinimum': 0, 'exclusiveMaximum': 100},
        ),
        (
            Annotated[int, parse(int).gt(0) | parse(int).lt(100)],
            {'anyOf': [{'type': 'integer', 'exclusiveMinimum': 0}, {'type': 'integer', 'exclusiveMaximum': 100}]},
            {'anyOf': [{'type': 'integer', 'exclusiveMinimum': 0}, {'type': 'integer', 'exclusiveMaximum': 100}]},
        ),
        (
            Annotated[list[int], parse().len(0, 100)],
            {'type': 'array', 'items': {'type': 'integer'}, 'maxItems': 100},
            {'type': 'array', 'items': {'type': 'integer'}, 'maxItems': 100},
        ),
    ],
)
def test_json_schema(
    model: type[Any], expected_val_schema: dict[str, Any], expected_ser_schema: dict[str, Any]
) -> None:
    ta = TypeAdapter(model)

    schema = ta.json_schema(mode='validation')
    assert schema == expected_val_schema

    schema = ta.json_schema(mode='serialization')
    assert schema == expected_ser_schema
