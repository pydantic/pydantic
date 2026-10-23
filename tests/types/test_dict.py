import json
from datetime import time, timedelta, timezone
from enum import Enum, Flag, IntFlag, auto
from typing import Annotated, Any, Literal

import pytest

from pydantic import ConfigDict, Field, TypeAdapter, ValidationError


def test_dict():
    ta = TypeAdapter(dict)

    assert ta.validate_python({1: 10, 2: 20}) == {1: 10, 2: 20}
    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python([(1, 2), (3, 4)])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'dict_type',
            'loc': (),
            'msg': 'Input should be a valid dictionary',
            'input': [(1, 2), (3, 4)],
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python([1, 2, 3])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'dict_type', 'loc': (), 'msg': 'Input should be a valid dictionary', 'input': [1, 2, 3]}
    ]


def test_dict_validate_json():
    ta = TypeAdapter(dict[int, int])

    assert ta.validate_json('{"1": 2, "3": 4}') == {1: 2, 3: 4}

    # duplicate keys, the last value wins, like with python
    assert json.loads('{"1": 1, "1": 2}') == {'1': 2}
    assert ta.validate_json('{"1": 1, "1": 2}') == {1: 2}


def test_dict_validate_json_any_value():
    ta = TypeAdapter(dict[str, Any])

    assert ta.validate_json('{"1": 1, "2": "a", "3": null}') == {'1': 1, '2': 'a', '3': None}


class NonStrEnum(Enum):
    INT = 200
    FLOAT = 0.5
    STR = 'b'


@pytest.mark.parametrize(
    ['key_type', 'value'],
    [
        (Literal[200, 0.5, 'b'], {200: 1, 0.5: 2, 'b': 3}),
        (NonStrEnum, {NonStrEnum.INT: 1, NonStrEnum.FLOAT: 2, NonStrEnum.STR: 3}),
    ],
)
@pytest.mark.parametrize('strict', [False, True])
def test_json_dict_non_str_literal_keys(key_type: Any, value: dict[Any, int], strict: bool) -> None:
    """https://github.com/pydantic/pydantic/issues/13988"""
    ta = TypeAdapter(dict[key_type, int])

    assert ta.dump_json(value) == b'{"200":1,"0.5":2,"b":3}'
    assert ta.validate_json(ta.dump_json(value), strict=strict) == value

    with pytest.raises(ValidationError, check=lambda v: v.errors()[0]['loc'] == ('201', '[key]')):
        ta.validate_json('{"201": 1}', strict=strict)

    # Only applies to JSON keys, not to Python inputs or JSON values:
    with pytest.raises(ValidationError):
        ta.validate_python({'200': 1}, strict=strict)
    with pytest.raises(ValidationError):
        TypeAdapter(dict[str, key_type]).validate_json('{"a": "200"}', strict=strict)


def test_json_dict_literal_keys_str_precedence() -> None:
    """String literal values take precedence over the string form of non-string ones."""
    assert TypeAdapter(dict[Literal[1, '1'], int]).validate_json('{"1": 1}') == {'1': 1}


@pytest.mark.parametrize(
    ['key_type', 'config', 'value', 'expected_json'],
    [
        (timedelta, ConfigDict(ser_json_timedelta='float'), timedelta(seconds=1.5), b'{"1.5":1}'),
        (timedelta, ConfigDict(ser_json_temporal='seconds'), timedelta(days=-2, seconds=3), b'{"-172797":1}'),
        (time, ConfigDict(ser_json_temporal='seconds'), time(1, 2, 3, 500_000, tzinfo=timezone.utc), b'{"3723.5":1}'),
    ],
)
@pytest.mark.parametrize('strict', [False, True])
def test_json_dict_numeric_temporal_keys(
    key_type: Any, config: ConfigDict, value: Any, expected_json: bytes, strict: bool
) -> None:
    """Temporal types serialized as numbers can only be represented as strings in JSON object keys."""
    ta = TypeAdapter(dict[key_type, int], config=config)

    assert ta.dump_json({value: 1}) == expected_json
    assert ta.validate_json(expected_json, strict=strict) == {value: 1}

    # Only applies to JSON keys, not to JSON values:
    with pytest.raises(ValidationError):
        TypeAdapter(key_type).validate_json(f'"{expected_json[2:-4].decode()}"', strict=strict)


class NoneEnum(Enum):
    NONE = None
    INT = 1


@pytest.mark.parametrize(
    ['key_type', 'value'],
    [
        (None, {None: 1}),
        (int | None, {None: 1, 2: 3}),
        (Literal[1, None], {None: 1, 1: 2}),
        (NoneEnum, {NoneEnum.NONE: 1, NoneEnum.INT: 2}),
    ],
)
@pytest.mark.parametrize('strict', [False, True])
def test_json_dict_none_keys(key_type: Any, value: dict[Any, int], strict: bool) -> None:
    """`None` keys are serialized as `"None"` in JSON."""
    ta = TypeAdapter(dict[key_type, int])

    assert ta.validate_json(ta.dump_json(value), strict=strict) == value

    # Only applies to JSON keys, not to Python inputs or JSON values:
    with pytest.raises(ValidationError):
        ta.validate_python({'None': 1}, strict=strict)
    with pytest.raises(ValidationError):
        TypeAdapter(dict[str, key_type]).validate_json('{"a": "None"}', strict=strict)


def test_json_dict_optional_str_none_key() -> None:
    """`"None"` is a valid string, so it takes precedence over `None`."""
    assert TypeAdapter(dict[str | None, int]).validate_json('{"None": 1}') == {'None': 1}

    # Also when `None` is the first member of a left-to-right union, as `None` is
    # extracted from the union (and validated last for JSON keys):
    ta = TypeAdapter(dict[Annotated[None | int | str, Field(union_mode='left_to_right')], int])
    assert ta.validate_json('{"None": 1}') == {'None': 1}


class Diet(Flag):
    ANIMALS = auto()
    LEAVES = auto()
    FRUIT = auto()
    HERBIVORE = LEAVES | FRUIT


class Permission(IntFlag):
    R = 4
    W = 2
    X = 1


@pytest.mark.parametrize(
    ['key_type', 'value'],
    [
        (Diet, {Diet.ANIMALS: 1, Diet.HERBIVORE: 2, Diet.ANIMALS | Diet.FRUIT: 3}),
        (Permission, {Permission.R: 1, Permission.R | Permission.X: 2}),
    ],
)
@pytest.mark.parametrize('strict', [False, True])
def test_json_dict_flag_keys(key_type: Any, value: dict[Any, int], strict: bool) -> None:
    """Combinations of flag members which aren't members themselves are validated from their string form.

    See https://github.com/pydantic/pydantic/issues/12448.
    """
    ta = TypeAdapter(dict[key_type, int])

    assert ta.validate_json(ta.dump_json(value), strict=strict) == value


def test_json_dict_flag_keys_invalid() -> None:
    ta = TypeAdapter(dict[Diet, int])

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_json('{"8": 1}')
    assert exc_info.value.errors(include_url=False)[0]['loc'] == ('8', '[key]')

    # Only applies to JSON keys, not to Python inputs or JSON values:
    with pytest.raises(ValidationError):
        ta.validate_python({'5': 1})
    with pytest.raises(ValidationError):
        TypeAdapter(Diet).validate_json('"5"')
