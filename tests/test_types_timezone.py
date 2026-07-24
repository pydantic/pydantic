from datetime import timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from pydantic import BaseModel, TypeAdapter, ValidationError


class TimezoneModel(BaseModel):
    tz: timezone


@pytest.mark.parametrize(
    'value,expected',
    [
        pytest.param('UTC', timezone.utc, id='utc-str'),
        pytest.param('utc', timezone.utc, id='utc-str-lowercase'),
        pytest.param('Z', timezone.utc, id='z-str'),
        pytest.param('UTC+05:00', timezone(timedelta(hours=5)), id='utc-offset-str'),
        pytest.param('UTC-08:30', timezone(timedelta(hours=-8, minutes=-30)), id='utc-negative-offset-str'),
        pytest.param('+05:00', timezone(timedelta(hours=5)), id='bare-offset-str'),
        pytest.param('-08:30', timezone(timedelta(hours=-8, minutes=-30)), id='bare-negative-offset-str'),
        pytest.param('UTC+05:00:30', timezone(timedelta(hours=5, seconds=30)), id='sub-minute-offset-str'),
    ],
)
def test_timezone_valid_inputs(value, expected):
    assert TimezoneModel(tz=value).tz == expected


def test_timezone_object_is_passed_through():
    tz = timezone(timedelta(hours=3))
    assert TimezoneModel(tz=tz).tz is tz


def test_timezone_python_mode_serialization_keeps_object():
    tz = timezone(timedelta(hours=3))
    assert TimezoneModel(tz=tz).model_dump()['tz'] is tz


@pytest.mark.parametrize(
    'value',
    [
        pytest.param('not-a-timezone', id='garbage-str'),
        pytest.param('', id='empty-str'),
        pytest.param('UTCfoo', id='utc-prefixed-garbage'),
        pytest.param(b'+05:00', id='bytes'),
        pytest.param(5, id='int'),
        pytest.param(None, id='none'),
        pytest.param(timedelta(hours=5), id='timedelta'),
    ],
)
def test_timezone_invalid_inputs(value):
    with pytest.raises(ValidationError):
        TimezoneModel(tz=value)


@pytest.mark.parametrize(
    'tz,expected',
    [
        pytest.param(timezone.utc, 'UTC', id='utc'),
        pytest.param(timezone(timedelta(hours=5)), 'UTC+05:00', id='positive'),
        pytest.param(timezone(timedelta(hours=-8, minutes=-30)), 'UTC-08:30', id='negative'),
        # A custom name is dropped in favor of the offset so the value round-trips.
        pytest.param(timezone(timedelta(hours=5, minutes=30), 'EST'), 'UTC+05:30', id='named-serializes-to-offset'),
        pytest.param(timezone(timedelta(hours=5, seconds=30)), 'UTC+05:00:30', id='sub-minute'),
    ],
)
def test_timezone_serialization(tz, expected):
    assert TimezoneModel(tz=tz).model_dump_json() == f'{{"tz":"{expected}"}}'


@pytest.mark.parametrize(
    'tz',
    [
        timezone.utc,
        timezone(timedelta(hours=5)),
        timezone(timedelta(hours=-8, minutes=-30)),
        timezone(timedelta(hours=5, minutes=30), 'EST'),
        timezone(timedelta(hours=5, seconds=30)),
        timezone(timedelta(seconds=-30)),
    ],
)
def test_timezone_round_trip(tz):
    ta = TypeAdapter(timezone)
    assert ta.validate_json(ta.dump_json(tz)).utcoffset(None) == tz.utcoffset(None)


def test_timezone_parsing_fails_for_invalid_strs():
    with pytest.raises(ValidationError) as exc_info:
        TimezoneModel(tz='not-a-timezone')
    assert exc_info.value.errors() == [
        {
            'type': 'timezone_parsing',
            'loc': ('tz',),
            'msg': 'Input is not a valid timezone: not-a-timezone',
            'input': 'not-a-timezone',
            'ctx': {'value': 'not-a-timezone'},
        }
    ]


def test_timezone_rejects_non_timezone_tzinfo():
    # A ZoneInfo is a tzinfo but not a datetime.timezone; the field is scoped to timezone.
    with pytest.raises(ValidationError):
        TimezoneModel(tz=ZoneInfo('America/Los_Angeles'))


def test_timezone_json_schema():
    assert TimezoneModel.model_json_schema() == {
        'type': 'object',
        'title': 'TimezoneModel',
        'properties': {'tz': {'type': 'string', 'format': 'timezone', 'title': 'Tz'}},
        'required': ['tz'],
    }
