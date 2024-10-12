"""
Tests for internal things that are complex enough to warrant their own unit tests.
"""

from dataclasses import dataclass
from decimal import Decimal

import pytest
from pydantic_core import CoreSchema
from pydantic_core import core_schema as cs

from pydantic._internal._core_utils import (
    Walk,
    collect_invalid_schemas,
    walk_core_schema,
)
from pydantic._internal._repr import Representation
from pydantic._internal._validators import _extract_decimal_digits_info


def remove_metadata(schema: CoreSchema) -> CoreSchema:
    def inner(s: CoreSchema, recurse: Walk) -> CoreSchema:
        s = s.copy()
        s.pop('metadata', None)
        return recurse(s, inner)

    return walk_core_schema(schema, inner)


def test_representation_integrations():
    devtools = pytest.importorskip('devtools')

    @dataclass
    class Obj(Representation):
        int_attr: int = 42
        str_attr: str = 'Marvin'

    obj = Obj()

    assert str(devtools.debug.format(obj)).split('\n')[1:] == [
        '    Obj(',
        '        int_attr=42,',
        "        str_attr='Marvin',",
        '    ) (Obj)',
    ]
    assert list(obj.__rich_repr__()) == [('int_attr', 42), ('str_attr', 'Marvin')]


def test_schema_is_valid():
    assert collect_invalid_schemas(cs.none_schema()) is False
    assert collect_invalid_schemas(cs.invalid_schema()) is True
    assert collect_invalid_schemas(cs.nullable_schema(cs.invalid_schema())) is True


@pytest.mark.parametrize(
    'decimal,decimal_places,digits',
    [
        (Decimal('0.0'), 1, 1),
        (Decimal('0.'), 0, 1),
        (Decimal('0.000'), 3, 3),
        (Decimal('0.0001'), 4, 4),
        (Decimal('.0001'), 4, 4),
        (Decimal('123.123'), 3, 6),
        (Decimal('123.1230'), 4, 7),
    ],
)
def test_decimal_digits_calculation(decimal: Decimal, decimal_places: int, digits: int) -> None:
    assert _extract_decimal_digits_info(decimal) == (decimal_places, digits)
