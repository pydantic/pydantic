"""Tests for the experimental transform module."""
from __future__ import annotations

import sys
import warnings
from datetime import datetime, timezone
from typing import Any, List, Union

import pytest
from typing_extensions import Annotated

if sys.version_info < (3, 9):
    from backports.zoneinfo import ZoneInfo
else:
    from zoneinfo import ZoneInfo

from pydantic import PydanticExperimentalWarning, TypeAdapter, ValidationError

with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=PydanticExperimentalWarning)
    from pydantic.experimental.pipeline import transform, validate_as


@pytest.mark.parametrize('potato_variation', ['potato', ' potato ', ' potato', 'potato ', ' POTATO ', ' PoTatO '])
def test_parse_str(potato_variation: str) -> None:
    ta_lower = TypeAdapter(Annotated[str, validate_as().str_strip().str_lower()])
    assert ta_lower.validate_python(potato_variation) == 'potato'


def test_parse_dt() -> None:
    expected = datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    ta = TypeAdapter(Annotated[datetime, validate_as().datetime_tz(timezone.utc)])
    assert ta.validate_json('"2000-01-01T00:00:00Z"') == expected
    with pytest.raises(ValidationError):
        ta.validate_json('"2000-01-01T00:00:00"')

    ta = TypeAdapter(Annotated[datetime, validate_as().transform(lambda x: x).datetime_tz(timezone.utc)])
    assert ta.validate_json('"2000-01-01T00:00:00Z"') == expected
    with pytest.raises(ValidationError):
        ta.validate_json('"2000-01-01T00:00:00"')

    ta = TypeAdapter(
        Annotated[
            datetime,
            validate_as().gt(datetime(1999, 1, 1, tzinfo=timezone.utc)).lt(datetime(2001, 1, 1, tzinfo=timezone.utc)),
        ]
    )
    assert ta.validate_json('"2000-01-01T00:00:00Z"') == expected
    with pytest.raises(ValidationError):
        ta.validate_json('"1988-01-01T00:00:00Z"')
    with pytest.raises(ValidationError):
        ta.validate_json('"2002-01-01T00:00:00Z"')


def test_unsupported_timezone() -> None:
    with pytest.raises(ValueError, match='timezone other than UTC is not supported'):
        TypeAdapter(Annotated[datetime, validate_as().datetime_tz(ZoneInfo('America/New_York'))])


def test_parse_str_with_pattern() -> None:
    ta_pattern = TypeAdapter(Annotated[str, validate_as().str_pattern(r'[a-z]+')])
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
    # annotated metadata is equivalent to validate_as(str).str_method(method_arg)
    # ex: validate_as(str).str_contains('pot')
    annotated_metadata = getattr(validate_as(str), 'str_' + method)
    annotated_metadata = annotated_metadata(method_arg) if method_arg else annotated_metadata()

    ta = TypeAdapter(Annotated[str, annotated_metadata])
    assert ta.validate_python(input_string) == expected_output


def test_string_validator_invalid() -> None:
    ta_contains = TypeAdapter(Annotated[str, validate_as(str).str_contains('potato')])
    with pytest.raises(ValidationError):
        ta_contains.validate_python('tomato')

    ta_starts_with = TypeAdapter(Annotated[str, validate_as(str).str_starts_with('potato')])
    with pytest.raises(ValidationError):
        ta_starts_with.validate_python('tomato')

    ta_ends_with = TypeAdapter(Annotated[str, validate_as(str).str_ends_with('potato')])
    with pytest.raises(ValidationError):
        ta_ends_with.validate_python('tomato')


def test_parse_int() -> None:
    ta_gt = TypeAdapter(Annotated[int, validate_as(int).gt(0)])
    assert ta_gt.validate_python(1) == 1
    assert ta_gt.validate_python('1') == 1
    with pytest.raises(ValidationError):
        ta_gt.validate_python(0)

    ta_gt_strict = TypeAdapter(Annotated[int, validate_as(int, strict=True).gt(0)])
    assert ta_gt_strict.validate_python(1) == 1
    with pytest.raises(ValidationError):
        ta_gt_strict.validate_python('1')
    with pytest.raises(ValidationError):
        ta_gt_strict.validate_python(0)


def test_parse_str_to_int() -> None:
    ta = TypeAdapter(Annotated[int, validate_as(str).str_strip().validate_as(int)])
    assert ta.validate_python('1') == 1
    assert ta.validate_python(' 1 ') == 1
    with pytest.raises(ValidationError):
        ta.validate_python('a')


def test_predicates() -> None:
    ta_int = TypeAdapter(Annotated[int, validate_as(int).predicate(lambda x: x % 2 == 0)])
    assert ta_int.validate_python(2) == 2
    with pytest.raises(ValidationError):
        ta_int.validate_python(1)

    ta_str = TypeAdapter(Annotated[str, validate_as(str).predicate(lambda x: x != 'potato')])
    assert ta_str.validate_python('tomato') == 'tomato'
    with pytest.raises(ValidationError):
        ta_str.validate_python('potato')


@pytest.mark.parametrize(
    'model, expected_val_schema, expected_ser_schema',
    [
        (
            Annotated[Union[int, str], validate_as() | validate_as(str)],
            {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
            {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
        ),
        (
            Annotated[int, validate_as() | validate_as(str).validate_as(int)],
            {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
            {'type': 'integer'},
        ),
        (
            Annotated[int, validate_as() | validate_as(str).transform(int)],
            {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
            {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
        ),
        (
            Annotated[int, validate_as() | validate_as(str).transform(int).validate_as(int)],
            {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
            {'type': 'integer'},
        ),
        (
            Annotated[int, validate_as(int).gt(0).lt(100)],
            {'type': 'integer', 'exclusiveMinimum': 0, 'exclusiveMaximum': 100},
            {'type': 'integer', 'exclusiveMinimum': 0, 'exclusiveMaximum': 100},
        ),
        (
            Annotated[int, validate_as(int).gt(0) | validate_as(int).lt(100)],
            {'anyOf': [{'type': 'integer', 'exclusiveMinimum': 0}, {'type': 'integer', 'exclusiveMaximum': 100}]},
            {'anyOf': [{'type': 'integer', 'exclusiveMinimum': 0}, {'type': 'integer', 'exclusiveMaximum': 100}]},
        ),
        (
            Annotated[List[int], validate_as().len(0, 100)],
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


def test_transform_first_step() -> None:
    """Check that when transform() is used as the first step in a pipeline it run after parsing."""
    ta = TypeAdapter(Annotated[int, transform(lambda x: x + 1)])
    assert ta.validate_python('1') == 2
