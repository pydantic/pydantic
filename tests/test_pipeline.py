"""Tests for the experimental transform module."""

from __future__ import annotations

import datetime
import sys
import warnings
from decimal import Decimal
from typing import Any, Callable, Dict, FrozenSet, List, Set, Tuple, Union

import pytest
import pytz
from annotated_types import Interval
from typing_extensions import Annotated

if sys.version_info >= (3, 9):
    pass

from pydantic import PydanticExperimentalWarning, TypeAdapter, ValidationError

with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=PydanticExperimentalWarning)
    from pydantic.experimental.pipeline import _Pipeline, transform, validate_as  # type: ignore


@pytest.mark.parametrize('potato_variation', ['potato', ' potato ', ' potato', 'potato ', ' POTATO ', ' PoTatO '])
def test_parse_str(potato_variation: str) -> None:
    ta_lower = TypeAdapter[str](Annotated[str, validate_as(...).str_strip().str_lower()])
    assert ta_lower.validate_python(potato_variation) == 'potato'


def test_parse_str_with_pattern() -> None:
    ta_pattern = TypeAdapter[str](Annotated[str, validate_as(...).str_pattern(r'[a-z]+')])
    assert ta_pattern.validate_python('potato') == 'potato'
    with pytest.raises(ValueError):
        ta_pattern.validate_python('POTATO')


@pytest.mark.parametrize(
    'type_, pipeline, valid_cases, invalid_cases',
    [
        (int, validate_as(...).ge(0), [0, 1, 100], [-1, -100]),
        (float, validate_as(...).ge(0.0), [1.8, 0.0], [-1.0]),
        (Decimal, validate_as(...).ge(Decimal(0.0)), [Decimal(1), Decimal(0.0)], [Decimal(-1.0)]),
        (int, validate_as(...).le(5), [2, 4], [6, 100]),
        (float, validate_as(...).le(1.0), [0.5, 0.0], [100.0]),
        (Decimal, validate_as(...).le(Decimal(1.0)), [Decimal(1)], [Decimal(5.0)]),
        (int, validate_as(...).gt(0), [1, 2, 100], [0, -1]),
        (float, validate_as(...).gt(0.0), [0.1, 1.8], [0.0, -1.0]),
        (Decimal, validate_as(...).gt(Decimal(0.0)), [Decimal(1)], [Decimal(0.0), Decimal(-1.0)]),
        (int, validate_as(...).lt(5), [2, 4], [5, 6, 100]),
        (float, validate_as(...).lt(1.0), [0.5, 0.0], [1.0, 100.0]),
        (Decimal, validate_as(...).lt(Decimal(1.0)), [Decimal(0.5)], [Decimal(1.0), Decimal(5.0)]),
    ],
)
def test_ge_le_gt_lt(
    type_: Any, pipeline: _Pipeline[Any, Any], valid_cases: list[Any], invalid_cases: list[Any]
) -> None:
    ta = TypeAdapter[Any](Annotated[type_, pipeline])
    for x in valid_cases:
        assert ta.validate_python(x) == x
    for y in invalid_cases:
        with pytest.raises(ValueError):
            ta.validate_python(y)


@pytest.mark.parametrize(
    'type_, pipeline, valid_cases, invalid_cases',
    [
        (int, validate_as(int).multiple_of(5), [5, 20, 0], [18, 7]),
        (float, validate_as(float).multiple_of(2.5), [2.5, 5.0, 7.5], [3.0, 1.1]),
        (
            Decimal,
            validate_as(Decimal).multiple_of(Decimal('1.5')),
            [Decimal('1.5'), Decimal('3.0'), Decimal('4.5')],
            [Decimal('1.4'), Decimal('2.1')],
        ),
    ],
)
def test_parse_multipleOf(type_: Any, pipeline: Any, valid_cases: list[Any], invalid_cases: list[Any]) -> None:
    ta = TypeAdapter[Any](Annotated[type_, pipeline])
    for x in valid_cases:
        assert ta.validate_python(x) == x
    for y in invalid_cases:
        with pytest.raises(ValueError):
            ta.validate_python(y)


@pytest.mark.parametrize(
    'type_, pipeline, valid_cases, invalid_cases',
    [
        (int, validate_as(int).constrain(Interval(ge=0, le=10)), [0, 5, 10], [11]),
        (float, validate_as(float).constrain(Interval(gt=0.0, lt=10.0)), [0.1, 9.9], [10.0]),
        (
            Decimal,
            validate_as(Decimal).constrain(Interval(ge=Decimal('1.0'), lt=Decimal('10.0'))),
            [Decimal('1.0'), Decimal('5.5'), Decimal('9.9')],
            [Decimal('0.0'), Decimal('10.0')],
        ),
        (int, validate_as(int).constrain(Interval(gt=1, lt=5)), [2, 4], [1, 5]),
        (float, validate_as(float).constrain(Interval(ge=1.0, le=5.0)), [1.0, 3.0, 5.0], [0.9, 5.1]),
    ],
)
def test_interval_constraints(type_: Any, pipeline: Any, valid_cases: list[Any], invalid_cases: list[Any]) -> None:
    ta = TypeAdapter[Any](Annotated[type_, pipeline])
    for x in valid_cases:
        assert ta.validate_python(x) == x
    for y in invalid_cases:
        with pytest.raises(ValueError):
            ta.validate_python(y)


@pytest.mark.parametrize(
    'type_, pipeline, valid_cases, invalid_cases',
    [
        (
            str,
            validate_as(str).len(min_len=2, max_len=5),
            ['ab', 'abc', 'abcd', 'abcde'],
            ['a', 'abcdef'],
        ),
        (
            List[int],
            validate_as(List[int]).len(min_len=1, max_len=3),
            [[1], [1, 2], [1, 2, 3]],
            [[], [1, 2, 3, 4]],
        ),
        (Tuple[int, ...], validate_as(Tuple[int, ...]).len(min_len=1, max_len=2), [(1,), (1, 2)], [(), (1, 2, 3)]),
        (
            Set[int],
            validate_as(Set[int]).len(min_len=2, max_len=4),
            [{1, 2}, {1, 2, 3}, {1, 2, 3, 4}],
            [{1}, {1, 2, 3, 4, 5}],
        ),
        (
            FrozenSet[int],
            validate_as(FrozenSet[int]).len(min_len=2, max_len=3),
            [frozenset({1, 2}), frozenset({1, 2, 3})],
            [frozenset({1}), frozenset({1, 2, 3, 4})],
        ),
        (
            Dict[str, int],
            validate_as(Dict[str, int]).len(min_len=1, max_len=2),
            [{'a': 1}, {'a': 1, 'b': 2}],
            [{}, {'a': 1, 'b': 2, 'c': 3}],
        ),
        (
            str,
            validate_as(str).len(min_len=2),  # max_len is None
            ['ab', 'abc', 'abcd', 'abcde', 'abcdef'],
            ['a'],
        ),
    ],
)
def test_len_constraints(type_: Any, pipeline: Any, valid_cases: list[Any], invalid_cases: list[Any]) -> None:
    ta = TypeAdapter[Any](Annotated[type_, pipeline])
    for x in valid_cases:
        assert ta.validate_python(x) == x
    for y in invalid_cases:
        with pytest.raises(ValueError):
            ta.validate_python(y)


def test_parse_tz() -> None:
    ta_tz = TypeAdapter[datetime.datetime](
        Annotated[
            datetime.datetime,
            validate_as(datetime.datetime).datetime_tz_naive(),
        ]
    )
    date = datetime.datetime(2032, 6, 4, 11, 15, 30, 400000)
    assert ta_tz.validate_python(date) == date
    date_a = datetime.datetime(2032, 6, 4, 11, 15, 30, 400000, tzinfo=pytz.UTC)
    with pytest.raises(ValueError):
        ta_tz.validate_python(date_a)

    ta_tza = TypeAdapter[datetime.datetime](
        Annotated[
            datetime.datetime,
            validate_as(datetime.datetime).datetime_tz_aware(),
        ]
    )
    date_a = datetime.datetime(2032, 6, 4, 11, 15, 30, 400000, pytz.UTC)
    assert ta_tza.validate_python(date_a) == date_a
    with pytest.raises(ValueError):
        ta_tza.validate_python(date)


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

    ta = TypeAdapter[str](Annotated[str, annotated_metadata])
    assert ta.validate_python(input_string) == expected_output


def test_string_validator_invalid() -> None:
    ta_contains = TypeAdapter[str](Annotated[str, validate_as(str).str_contains('potato')])
    with pytest.raises(ValidationError):
        ta_contains.validate_python('tomato')

    ta_starts_with = TypeAdapter[str](Annotated[str, validate_as(str).str_starts_with('potato')])
    with pytest.raises(ValidationError):
        ta_starts_with.validate_python('tomato')

    ta_ends_with = TypeAdapter[str](Annotated[str, validate_as(str).str_ends_with('potato')])
    with pytest.raises(ValidationError):
        ta_ends_with.validate_python('tomato')


def test_parse_int() -> None:
    ta_gt = TypeAdapter[int](Annotated[int, validate_as(int).gt(0)])
    assert ta_gt.validate_python(1) == 1
    assert ta_gt.validate_python('1') == 1
    with pytest.raises(ValidationError):
        ta_gt.validate_python(0)

    ta_gt_strict = TypeAdapter[int](Annotated[int, validate_as(int, strict=True).gt(0)])
    assert ta_gt_strict.validate_python(1) == 1
    with pytest.raises(ValidationError):
        ta_gt_strict.validate_python('1')
    with pytest.raises(ValidationError):
        ta_gt_strict.validate_python(0)


def test_parse_str_to_int() -> None:
    ta = TypeAdapter[int](Annotated[int, validate_as(str).str_strip().validate_as(int)])
    assert ta.validate_python('1') == 1
    assert ta.validate_python(' 1 ') == 1
    with pytest.raises(ValidationError):
        ta.validate_python('a')


def test_predicates() -> None:
    ta_int = TypeAdapter[int](Annotated[int, validate_as(int).predicate(lambda x: x % 2 == 0)])
    assert ta_int.validate_python(2) == 2
    with pytest.raises(ValidationError):
        ta_int.validate_python(1)

    ta_str = TypeAdapter[int](Annotated[str, validate_as(str).predicate(lambda x: x != 'potato')])
    assert ta_str.validate_python('tomato') == 'tomato'
    with pytest.raises(ValidationError):
        ta_str.validate_python('potato')


@pytest.mark.parametrize(
    'model, expected_val_schema, expected_ser_schema',
    [
        (
            Annotated[Union[int, str], validate_as(...) | validate_as(str)],
            {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
            {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
        ),
        (
            Annotated[int, validate_as(...) | validate_as(str).validate_as(int)],
            {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
            {'type': 'integer'},
        ),
        (
            Annotated[int, validate_as(...) | validate_as(str).validate_as(int)],
            {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
            {'type': 'integer'},
        ),
        (
            Annotated[int, validate_as(...) | validate_as(str).transform(int).validate_as(int)],
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
            Annotated[List[int], validate_as(...).len(0, 100)],
            {'type': 'array', 'items': {'type': 'integer'}, 'maxItems': 100},
            {'type': 'array', 'items': {'type': 'integer'}, 'maxItems': 100},
        ),
        # note - we added this to confirm the fact that the transform doesn't impact the JSON schema,
        # as it's applied as a function after validator
        (
            Annotated[int, validate_as(str).transform(int)],
            {'type': 'string'},
            {'type': 'string'},  # see this is still string
        ),
        # in juxtaposition to the case above, when we use validate_as (recommended),
        # the JSON schema is updated appropriately
        (
            Annotated[int, validate_as(str).validate_as(int)],
            {'type': 'string'},
            {'type': 'integer'},  # aha, this is now an integer
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
    ta = TypeAdapter[int](Annotated[int, transform(lambda x: x + 1)])
    assert ta.validate_python('1') == 2


def test_not_eq() -> None:
    ta = TypeAdapter[int](Annotated[str, validate_as(str).not_eq('potato')])
    assert ta.validate_python('tomato') == 'tomato'
    with pytest.raises(ValidationError):
        ta.validate_python('potato')


def test_eq() -> None:
    ta = TypeAdapter[int](Annotated[str, validate_as(str).eq('potato')])
    assert ta.validate_python('potato') == 'potato'
    with pytest.raises(ValidationError):
        ta.validate_python('tomato')


def test_not_in() -> None:
    ta = TypeAdapter[int](Annotated[str, validate_as(str).not_in(['potato', 'tomato'])])
    assert ta.validate_python('carrot') == 'carrot'
    with pytest.raises(ValidationError):
        ta.validate_python('potato')


def test_in() -> None:
    ta = TypeAdapter[int](Annotated[str, validate_as(str).in_(['potato', 'tomato'])])
    assert ta.validate_python('potato') == 'potato'
    with pytest.raises(ValidationError):
        ta.validate_python('carrot')


def test_composition() -> None:
    ta = TypeAdapter[int](Annotated[int, validate_as(int).gt(10) | validate_as(int).lt(5)])
    assert ta.validate_python(1) == 1
    assert ta.validate_python(20) == 20
    with pytest.raises(ValidationError):
        ta.validate_python(9)

    ta = TypeAdapter[int](Annotated[int, validate_as(int).gt(10) & validate_as(int).le(20)])
    assert ta.validate_python(15) == 15
    with pytest.raises(ValidationError):
        ta.validate_python(9)
    with pytest.raises(ValidationError):
        ta.validate_python(21)

    # test that sticking a transform in the middle doesn't break the composition
    calls: list[tuple[str, int]] = []

    def tf(step: str) -> Callable[[int], int]:
        def inner(x: int) -> int:
            calls.append((step, x))
            return x

        return inner

    ta = TypeAdapter[int](
        Annotated[
            int,
            validate_as(int).transform(tf('1')).gt(10).transform(tf('2'))
            | validate_as(int).transform(tf('3')).lt(5).transform(tf('4')),
        ]
    )
    assert ta.validate_python(1) == 1
    assert calls == [('1', 1), ('3', 1), ('4', 1)]
    calls.clear()
    assert ta.validate_python(20) == 20
    assert calls == [('1', 20), ('2', 20)]
    calls.clear()
    with pytest.raises(ValidationError):
        ta.validate_python(9)
    assert calls == [('1', 9), ('3', 9)]
    calls.clear()

    ta = TypeAdapter[int](
        Annotated[
            int,
            validate_as(int).transform(tf('1')).gt(10).transform(tf('2'))
            & validate_as(int).transform(tf('3')).le(20).transform(tf('4')),
        ]
    )
    assert ta.validate_python(15) == 15
    assert calls == [('1', 15), ('2', 15), ('3', 15), ('4', 15)]
    calls.clear()
    with pytest.raises(ValidationError):
        ta.validate_python(9)
    assert calls == [('1', 9)]
    calls.clear()
    with pytest.raises(ValidationError):
        ta.validate_python(21)
    assert calls == [('1', 21), ('2', 21), ('3', 21)]
    calls.clear()
