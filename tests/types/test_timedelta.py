from datetime import timedelta
from decimal import Decimal
from typing import Annotated

import pytest
from pydantic_core import SchemaError

from pydantic import Field, TypeAdapter, ValidationError


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
    ta = TypeAdapter(timedelta)

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            ta.validate_python(value)
    else:
        assert ta.validate_python(value) == expected


def test_timedelta_parsing_error():
    ta = TypeAdapter(timedelta)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('15:30.0001broken')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'time_delta_parsing',
            'loc': (),
            'msg': 'Input should be a valid timedelta, unexpected extra characters at the end of the input',
            'input': '15:30.0001broken',
            'ctx': {'error': 'unexpected extra characters at the end of the input'},
        }
    ]


def test_strict_timedelta():
    ta = TypeAdapter(Annotated[timedelta, Field(strict=True)])

    assert ta.validate_python(timedelta(days=1)) == timedelta(days=1)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('1 days')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'time_delta_type',
            'loc': (),
            'msg': 'Input should be a valid timedelta',
            'input': '1 days',
        }
    ]


@pytest.mark.parametrize(
    'value',
    [timedelta(0), timedelta(minutes=45), timedelta(minutes=-30), timedelta(days=3), 'PT1H', 900],
)
def test_timedelta_multiple_of(value: object) -> None:

    ta = TypeAdapter(Annotated[timedelta, Field(multiple_of=timedelta(minutes=15))])
    assert ta.validate_python(value) % timedelta(minutes=15) == timedelta(0)


def test_timedelta_multiple_of_error() -> None:
    ta = TypeAdapter(Annotated[timedelta, Field(multiple_of=timedelta(minutes=15))])

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python(timedelta(minutes=50))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'multiple_of',
            'loc': (),
            'msg': 'Input should be a multiple of 15 minutes',
            'input': timedelta(minutes=50),
            'ctx': {'multiple_of': '15 minutes'},
        }
    ]


@pytest.mark.parametrize('multiple_of', [timedelta(0), timedelta(minutes=-15)])
def test_timedelta_multiple_of_invalid_constraint(multiple_of: timedelta) -> None:
    """https://github.com/pydantic/pydantic/issues/13868"""

    with pytest.raises(SchemaError, match="'multiple_of' must be greater than 0"):
        TypeAdapter(Annotated[timedelta, Field(multiple_of=multiple_of)])
