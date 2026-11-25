"""Fixed schema handlers keep returned schemas independent."""

import collections.abc
import datetime
from decimal import Decimal
from fractions import Fraction
from types import EllipsisType
from typing import Any
from uuid import UUID

import pytest
from pydantic_core import MISSING, MultiHostUrl, Url

from pydantic import TypeAdapter


@pytest.mark.parametrize(
    ('annotation', 'schema'),
    [
        (datetime.date, {'type': 'date'}),
        (datetime.datetime, {'type': 'datetime', 'microseconds_precision': 'truncate'}),
        (datetime.time, {'type': 'time', 'microseconds_precision': 'truncate'}),
        (datetime.timedelta, {'type': 'timedelta', 'microseconds_precision': 'truncate'}),
        (Decimal, {'type': 'decimal'}),
        (UUID, {'type': 'uuid'}),
        (Url, {'type': 'url'}),
        (Fraction, {'type': 'fraction'}),
        (MultiHostUrl, {'type': 'multi-host-url'}),
        (object, {'type': 'any'}),
        (MISSING, {'type': 'missing-sentinel'}),
        (EllipsisType, {'type': 'ellipsis'}),
        (collections.abc.Callable, {'type': 'callable'}),
        (collections.abc.Callable[[int], str], {'type': 'callable'}),
    ],
)
def test_fixed_schema_is_independent(annotation: Any, schema: dict[str, Any]) -> None:
    first = TypeAdapter(annotation).core_schema
    first['metadata'] = {'changed': True}

    assert TypeAdapter(annotation).core_schema == schema
