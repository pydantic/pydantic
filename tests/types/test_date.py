from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

import pytest

from pydantic import BaseModel, Field, ValidationError


@pytest.mark.parametrize(
    'value,expected',
    [
        (date(2017, 5, 5), date(2017, 5, 5)),
        (datetime(2017, 5, 5), date(2017, 5, 5)),
        pytest.param('2017-05-05', date(2017, 5, 5), id='2017-05-05_str'),
        pytest.param(b'2017-05-05', date(2017, 5, 5), id='2017-05-05_bytes'),
        (1493942400000, date(2017, 5, 5)),
        (1493942400, date(2017, 5, 5)),
        (1493942400000.0, date(2017, 5, 5)),
        (Decimal(1493942400000), date(2017, 5, 5)),
        (datetime(2017, 5, 5, 10), ValidationError),
        pytest.param('2017-5-5', ValidationError, id='2017-5-5_str'),
        pytest.param(b'2017-5-5', ValidationError, id='2017-5-5_bytes'),
        (1493942401000, ValidationError),
        (1493942401000.0, ValidationError),
        (Decimal(1493942401000), ValidationError),
    ],
)
def test_date_validation(value, expected):
    class Model(BaseModel):
        v: date

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            Model(v=value)
    else:
        assert Model(v=value).v == expected


def test_date_parsing_error():
    class Model(BaseModel):
        v: date

    with pytest.raises(ValidationError) as exc_info:
        Model(v='XX1494012000')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'date_from_datetime_parsing',
            'loc': ('v',),
            'msg': 'Input should be a valid date or datetime, invalid character in year',
            'input': 'XX1494012000',
            'ctx': {'error': 'invalid character in year'},
        }
    ]


def test_strict_date():
    class Model(BaseModel):
        v: Annotated[date, Field(strict=True)]

    assert Model(v=date(2017, 5, 5)).v == date(2017, 5, 5)

    with pytest.raises(ValidationError) as exc_info:
        Model(v=datetime(2017, 5, 5))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'date_type',
            'loc': ('v',),
            'msg': 'Input should be a valid date',
            'input': datetime(2017, 5, 5),
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model(v='2017-05-05')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'date_type',
            'loc': ('v',),
            'msg': 'Input should be a valid date',
            'input': '2017-05-05',
        }
    ]
