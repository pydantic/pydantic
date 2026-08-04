from datetime import time, timezone
from decimal import Decimal
from typing import Annotated

import pytest

from pydantic import Field, TypeAdapter, ValidationError


@pytest.mark.parametrize(
    'value,expected',
    [
        (time(10, 10, 10), time(10, 10, 10)),
        ('10:10:10.0002', time(10, 10, 10, microsecond=200)),
        (b'10:10:10.0002', time(10, 10, 10, microsecond=200)),
        (3720, time(1, 2, tzinfo=timezone.utc)),
        (3720.0002, time(1, 2, microsecond=200, tzinfo=timezone.utc)),
        (Decimal(3720.0002), time(1, 2, microsecond=200, tzinfo=timezone.utc)),
        pytest.param('1:1:1', ValidationError, id='1:1:1_str'),
        pytest.param(b'1:1:1', ValidationError, id='1:1:1_bytes'),
        (-1, ValidationError),
        (86400, ValidationError),
        (86400.0, ValidationError),
        (Decimal(86400), ValidationError),
    ],
)
def test_time_validation(value, expected):
    ta = TypeAdapter(time)

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            ta.validate_python(value)
    else:
        assert ta.validate_python(value) == expected


def test_time_parsing_error():
    ta = TypeAdapter(time)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('25:20:30.400')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'time_parsing',
            'loc': (),
            'msg': 'Input should be in a valid time format, hour value is outside expected range of 0-23',
            'input': '25:20:30.400',
            'ctx': {'error': 'hour value is outside expected range of 0-23'},
        }
    ]


def test_strict_time():
    ta = TypeAdapter(Annotated[time, Field(strict=True)])

    assert ta.validate_python(time(10, 10, 10)) == time(10, 10, 10)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('10:10:10')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'time_type',
            'loc': (),
            'msg': 'Input should be a valid time',
            'input': '10:10:10',
        }
    ]
