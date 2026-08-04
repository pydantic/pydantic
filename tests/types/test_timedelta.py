from datetime import timedelta
from decimal import Decimal
from typing import Annotated

import pytest

from pydantic import BaseModel, Field, ValidationError


@pytest.mark.parametrize(
    'value,expected',
    [
        (timedelta(days=1), timedelta(days=1)),
        ('1 days 10:10', timedelta(days=1, seconds=36600)),
        ('1 d 10:10', timedelta(days=1, seconds=36600)),
        (b'1 days 10:10', timedelta(days=1, seconds=36600)),
        (123_000, timedelta(days=1, seconds=36600)),
        (123_000.0002, timedelta(days=1, seconds=36600, microseconds=200)),
        (Decimal(123_000.0002), timedelta(days=1, seconds=36600, microseconds=200)),
        pytest.param('1 10:10', ValidationError, id='1 10:10_str'),
        pytest.param(b'1 10:10', ValidationError, id='1 10:10_bytes'),
    ],
)
def test_timedelta_validation(value, expected):
    class Model(BaseModel):
        v: timedelta

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            Model(v=value)
    else:
        assert Model(v=value).v == expected


def test_timedelta_parsing_error():
    class Model(BaseModel):
        v: timedelta

    with pytest.raises(ValidationError) as exc_info:
        Model(v='15:30.0001broken')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'time_delta_parsing',
            'loc': ('v',),
            'msg': 'Input should be a valid timedelta, unexpected extra characters at the end of the input',
            'input': '15:30.0001broken',
            'ctx': {'error': 'unexpected extra characters at the end of the input'},
        }
    ]


def test_strict_timedelta():
    class Model(BaseModel):
        v: Annotated[timedelta, Field(strict=True)]

    assert Model(v=timedelta(days=1)).v == timedelta(days=1)

    with pytest.raises(ValidationError) as exc_info:
        Model(v='1 days')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'time_delta_type',
            'loc': ('v',),
            'msg': 'Input should be a valid timedelta',
            'input': '1 days',
        }
    ]
