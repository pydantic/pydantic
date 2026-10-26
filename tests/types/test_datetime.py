from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Annotated

import pytest

from pydantic import Field, TypeAdapter, ValidationError


@pytest.mark.parametrize(
    'value,expected',
    [
        (datetime(2017, 5, 5, 10, 10, 10), datetime(2017, 5, 5, 10, 10, 10)),
        (date(2017, 5, 5), datetime(2017, 5, 5, 0, 0, 0)),
        pytest.param(
            '2017-05-05T10:10:10.0002',
            datetime(2017, 5, 5, 10, 10, 10, microsecond=200),
            id='2017-05-05T10:10:10.0002_str',
        ),
        ('2017-05-05 10:10:10', datetime(2017, 5, 5, 10, 10, 10)),
        ('2017-05-05 10:10:10+00:00', datetime(2017, 5, 5, 10, 10, 10, tzinfo=timezone.utc)),
        pytest.param(
            b'2017-05-05T10:10:10.0002',
            datetime(2017, 5, 5, 10, 10, 10, microsecond=200),
            id='2017-05-05T10:10:10.0002_bytes',
        ),
        (1493979010000, datetime(2017, 5, 5, 10, 10, 10, tzinfo=timezone.utc)),
        (1493979010, datetime(2017, 5, 5, 10, 10, 10, tzinfo=timezone.utc)),
        (1493979010000.0, datetime(2017, 5, 5, 10, 10, 10, tzinfo=timezone.utc)),
        (Decimal(1493979010), datetime(2017, 5, 5, 10, 10, 10, tzinfo=timezone.utc)),
        pytest.param('2017-5-5T10:10:10', ValidationError, id='2017-5-5T10:10:10_str'),
        pytest.param(b'2017-5-5T10:10:10', ValidationError, id='2017-5-5T10:10:10_bytes'),
    ],
)
def test_datetime_validation(value, expected):
    ta = TypeAdapter(datetime)

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            ta.validate_python(value)
    else:
        assert ta.validate_python(value) == expected


def test_datetime_parsing_error():
    ta = TypeAdapter(datetime)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('2017-13-05T19:47:07')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'datetime_from_date_parsing',
            'loc': (),
            'msg': 'Input should be a valid datetime or date, month value is outside expected range of 1-12',
            'input': '2017-13-05T19:47:07',
            'ctx': {'error': 'month value is outside expected range of 1-12'},
        }
    ]


def test_strict_datetime():
    ta = TypeAdapter(Annotated[datetime, Field(strict=True)])

    assert ta.validate_python(datetime(2017, 5, 5, 10, 10, 10)) == datetime(2017, 5, 5, 10, 10, 10)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(date(2017, 5, 5))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'datetime_type',
            'loc': (),
            'msg': 'Input should be a valid datetime',
            'input': date(2017, 5, 5),
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('2017-05-05T10:10:10')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'datetime_type',
            'loc': (),
            'msg': 'Input should be a valid datetime',
            'input': '2017-05-05T10:10:10',
        }
    ]
