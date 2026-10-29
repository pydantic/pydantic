"""Fixed schema handlers keep returned schemas independent."""

import datetime
from decimal import Decimal
from fractions import Fraction
from typing import Any
from uuid import UUID

import pytest
from pydantic_core import MultiHostUrl, Url

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
    ],
)
def test_fixed_schema_is_independent(annotation: Any, schema: dict[str, Any]) -> None:
    first = TypeAdapter(annotation).core_schema
    first['metadata'] = {'changed': True}

    assert TypeAdapter(annotation).core_schema == schema
