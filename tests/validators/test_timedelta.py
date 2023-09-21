import re
from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError, validate_core_schema

from ..conftest import Err, PyAndJson

try:
    import pandas
except ImportError:
    pandas = None


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (
            timedelta(days=-3, hours=2, seconds=1, milliseconds=500),
            timedelta(days=-3, hours=2, seconds=1, milliseconds=500),
        ),
        (
            timedelta(days=3, weeks=2, hours=1, minutes=2, seconds=3, milliseconds=500),
            timedelta(days=3, weeks=2, hours=1, minutes=2, seconds=3, milliseconds=500),
        ),
        ('P0Y0M3D2WT1H2M3.5S', timedelta(days=3, weeks=2, hours=1, minutes=2, seconds=3, milliseconds=500)),
        (b'P0Y0M3D2WT1H2M3.5S', timedelta(days=3, weeks=2, hours=1, minutes=2, seconds=3, milliseconds=500)),
        ((-1,), Err('Input should be a valid timedelta [type=time_delta_type')),
        (
            b'-1',
            Err(
                'Input should be a valid timedelta, "day" identifier in duration '
                'not correctly formatted [type=time_delta_parsing'
            ),
        ),
        (3601, timedelta(hours=1, seconds=1)),
        (Decimal('3601.123456'), timedelta(hours=1, seconds=1, microseconds=123456)),
        (Decimal('3601.1234562'), timedelta(hours=1, seconds=1, microseconds=123456)),
        (Decimal('3601.1234568'), timedelta(hours=1, seconds=1, microseconds=123457)),
        (-3601, timedelta(hours=-2, seconds=3599)),
        (Decimal('-3601.222222'), timedelta(hours=-2, seconds=3598, microseconds=777778)),
        (Decimal('-3601.2222222'), timedelta(hours=-2, seconds=3598, microseconds=777778)),
        (Decimal('-3601.2222227'), timedelta(hours=-2, seconds=3598, microseconds=777777)),
        (float('nan'), Err('Input should be a valid timedelta, NaN values not permitted')),
        (float('inf'), Err('Input should be a valid timedelta, durations may not exceed 999,999,999 days')),
        (float('-inf'), Err('Input should be a valid timedelta, durations may not exceed 999,999,999 days')),
        (timedelta.max, timedelta.max),
        ('02:03:04.05', timedelta(hours=2, seconds=184, microseconds=50_000)),
        (
            '02:03:04.05broken',
            Err('Input should be a valid timedelta, unexpected extra characters at the end of the input'),
        ),
    ],
    ids=repr,
)
def test_timedelta(input_value, expected):
    v = SchemaValidator({'type': 'timedelta'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('"P0Y0M3D2WT1H2M3.5S"', timedelta(days=3, weeks=2, hours=1, minutes=2, seconds=3, milliseconds=500)),
        ('"errordata"', Err('Input should be a valid duration, invalid digit in duration [type=time_delta_parsing')),
        ('true', Err('Input should be a valid duration [type=time_delta_type')),
        ('3601', timedelta(hours=1, seconds=1)),
        ('3601.123456', timedelta(hours=1, seconds=1, microseconds=123456)),
        ('-3601', timedelta(hours=-2, seconds=3599)),
        ('-3601.222222', timedelta(hours=-2, seconds=3598, microseconds=777778)),
        ('-3601.2222222', timedelta(hours=-2, seconds=3598, microseconds=777778)),
        ('3600.999999', timedelta(seconds=3600, microseconds=999999)),
    ],
    ids=repr,
)
def test_timedelta_json(input_value, expected):
    v = SchemaValidator({'type': 'timedelta'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_json(input_value)
    else:
        output = v.validate_json(input_value)
        assert output == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (
            timedelta(days=3, weeks=2, hours=1, minutes=2, seconds=3, milliseconds=500),
            timedelta(days=3, weeks=2, hours=1, minutes=2, seconds=3, milliseconds=500),
        ),
        ('P0Y0M3D2WT1H2M3.5S', Err('Input should be a valid timedelta [type=time_delta_type')),
        (b'P0Y0M3D2WT1H2M3.5S', Err('Input should be a valid timedelta [type=time_delta_type')),
    ],
)
def test_timedelta_strict(input_value, expected):
    v = SchemaValidator({'type': 'timedelta', 'strict': True})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('"P0Y0M3D2WT1H2M3.5S"', timedelta(days=3, weeks=2, hours=1, minutes=2, seconds=3, milliseconds=500)),
        ('"12345"', Err('Input should be a valid duration')),
        ('true', Err('Input should be a valid duration [type=time_delta_type')),
    ],
)
def test_timedelta_strict_json(input_value, expected):
    v = SchemaValidator({'type': 'timedelta', 'strict': True})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_json(input_value)
    else:
        output = v.validate_json(input_value)
        assert output == expected


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({}, 'P0Y0M3D2WT1H2M3S', timedelta(days=3, weeks=2, hours=1, minutes=2, seconds=3)),
        ({'le': timedelta(days=3)}, 'P2DT1H', timedelta(days=2, hours=1)),
        ({'le': timedelta(days=3)}, 'P3DT0H', timedelta(days=3)),
        ({'le': timedelta(days=3)}, 'P3DT1H', Err('Input should be less than or equal to 3 days')),
        ({'lt': timedelta(days=3)}, 'P2DT1H', timedelta(days=2, hours=1)),
        ({'lt': timedelta(days=3)}, 'P3DT1H', Err('Input should be less than 3 days')),
        ({'ge': timedelta(days=3)}, 'P3DT1H', timedelta(days=3, hours=1)),
        ({'ge': timedelta(days=3)}, 'P3D', timedelta(days=3)),
        ({'ge': timedelta(days=3)}, 'P2DT1H', Err('Input should be greater than or equal to 3 days')),
        ({'gt': timedelta(days=3)}, 'P3DT1H', timedelta(days=3, hours=1)),
        ({'le': timedelta(seconds=-86400.123)}, '-PT86400.123S', timedelta(seconds=-86400.123)),
        ({'le': timedelta(seconds=-86400.123)}, '-PT86400.124S', timedelta(seconds=-86400.124)),
        (
            {'le': timedelta(seconds=-86400.123)},
            '-PT86400.122S',
            Err(
                'Input should be less than or equal to -2 days and 23 hours and 59 minutes and 59 seconds and 877000 microseconds [type=less_than_equal'
            ),
        ),
        ({'gt': timedelta(seconds=-86400.123)}, timedelta(seconds=-86400.122), timedelta(seconds=-86400.122)),
        ({'gt': timedelta(seconds=-86400.123)}, '-PT86400.122S', timedelta(seconds=-86400.122)),
        (
            {'gt': timedelta(seconds=-86400.123)},
            '-PT86400.124S',
            Err(
                'Input should be greater than -2 days and 23 hours and 59 minutes and 59 seconds and 877000 microseconds [type=greater_than'
            ),
        ),
        (
            {'gt': timedelta(hours=1, minutes=30)},
            'PT180S',
            Err('Input should be greater than 1 hour and 30 minutes [type=greater_than'),
        ),
        ({'gt': timedelta()}, '-P0DT0.1S', Err('Input should be greater than 0 seconds [type=greater_than')),
        ({'gt': timedelta()}, 'P0DT0.0S', Err('Input should be greater than 0 seconds [type=greater_than')),
        ({'ge': timedelta()}, 'P0DT0.0S', timedelta()),
        ({'lt': timedelta()}, '-PT0S', timedelta()),
        (
            {'lt': timedelta(days=740, weeks=1, hours=48, minutes=60, seconds=61, microseconds=100000)},
            'P2Y1W10DT48H60M61.100000S',
            Err('Input should be less than 749 days and 1 hour and 1 minute and 1 second and 100000 microseconds'),
        ),
    ],
    ids=repr,
)
def test_timedelta_kwargs(kwargs: Dict[str, Any], input_value, expected):
    v = SchemaValidator({'type': 'timedelta', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected


def test_timedelta_kwargs_strict():
    v = SchemaValidator({'type': 'timedelta', 'strict': True, 'le': timedelta(days=3)})
    output = v.validate_python(timedelta(days=2, hours=1))
    assert output == timedelta(days=2, hours=1)


def test_invalid_constraint():
    with pytest.raises(SchemaError, match='timedelta.gt\n  Input should be a valid timedelta, invalid digit in'):
        validate_core_schema({'type': 'timedelta', 'gt': 'foobar'})

    with pytest.raises(SchemaError, match='timedelta.le\n  Input should be a valid timedelta, invalid digit in'):
        validate_core_schema({'type': 'timedelta', 'le': 'foobar'})


def test_dict_py():
    v = SchemaValidator({'type': 'dict', 'keys_schema': {'type': 'timedelta'}, 'values_schema': {'type': 'int'}})
    assert v.validate_python({timedelta(days=2, hours=1): 2, timedelta(days=2, hours=2): 4}) == {
        timedelta(days=2, hours=1): 2,
        timedelta(days=2, hours=2): 4,
    }


def test_dict_key(py_and_json: PyAndJson):
    v = py_and_json({'type': 'dict', 'keys_schema': {'type': 'timedelta'}, 'values_schema': {'type': 'int'}})
    assert v.validate_test({'P2DT1H': 2, 'P2DT2H': 4}) == {timedelta(days=2, hours=1): 2, timedelta(days=2, hours=2): 4}

    with pytest.raises(ValidationError, match=re.escape('[type=time_delta_parsing')):
        v.validate_test({'errordata': 2})


def test_dict_value(py_and_json: PyAndJson):
    v = py_and_json({'type': 'dict', 'keys_schema': {'type': 'int'}, 'values_schema': {'type': 'timedelta'}})
    assert v.validate_test({2: 'P2DT1H', 4: 'P2DT2H'}) == {2: timedelta(days=2, hours=1), 4: timedelta(days=2, hours=2)}

    with pytest.raises(ValidationError, match=re.escape('[type=time_delta_parsing')):
        v.validate_test({4: 'errordata'})


def test_union():
    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'str'}, {'type': 'timedelta'}]})
    assert v.validate_python('P2DT1H') == 'P2DT1H'
    assert v.validate_python(timedelta(days=2, hours=1)) == timedelta(days=2, hours=1)

    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'timedelta'}, {'type': 'str'}]})
    assert v.validate_python('P2DT1H') == 'P2DT1H'
    assert v.validate_python(timedelta(days=2, hours=1)) == timedelta(days=2, hours=1)


@pytest.mark.parametrize(
    'constraint,expected_duration',
    [
        (timedelta(days=3), {'positive': True, 'day': 3, 'second': 0, 'microsecond': 0}),
        (timedelta(days=2, seconds=42.123), {'positive': True, 'day': 2, 'second': 42, 'microsecond': 123_000}),
        (timedelta(days=-1), {'positive': False, 'day': 1, 'second': 0, 'microsecond': 0}),
        (timedelta(seconds=86410), {'positive': True, 'day': 1, 'second': 10, 'microsecond': 0}),
        (timedelta(seconds=86410.123), {'positive': True, 'day': 1, 'second': 10, 'microsecond': 123_000}),
        (timedelta(seconds=-86410), {'positive': False, 'day': 1, 'second': 10, 'microsecond': 0}),
        (timedelta(seconds=-86410.123), {'positive': False, 'day': 1, 'second': 10, 'microsecond': 123_000}),
        (timedelta(days=-4, hours=12), {'positive': False, 'day': 3, 'second': 43200, 'microsecond': 0}),
        (timedelta(days=-4, microseconds=456), {'positive': False, 'day': 3, 'second': 86399, 'microsecond': 999544}),
        (timedelta(days=-1, seconds=20_000), {'positive': False, 'day': 0, 'second': 66_400, 'microsecond': 0}),
        (
            timedelta(days=-1, seconds=86_399, microseconds=1),
            {'positive': False, 'day': 0, 'second': 0, 'microsecond': 999_999},
        ),
        (timedelta.max, {'positive': True, 'day': 999999999, 'second': 86399, 'microsecond': 999999}),
        (timedelta.min, {'positive': False, 'day': 999999999, 'second': 0, 'microsecond': 0}),
    ],
    ids=repr,
)
def test_pytimedelta_as_timedelta(constraint, expected_duration):
    v = SchemaValidator({'type': 'timedelta', 'gt': constraint})
    # simplest way to check `pytimedelta_as_timedelta` is correct is to extract duration from repr of the validator
    m = re.search(r'Duration ?\{\s+positive: ?(\w+),\s+day: ?(\d+),\s+second: ?(\d+),\s+microsecond: ?(\d+)', repr(v))
    pos, day, sec, micro = m.groups()
    duration = {'positive': pos == 'true', 'day': int(day), 'second': int(sec), 'microsecond': int(micro)}
    assert duration == pytest.approx(expected_duration), constraint


def test_large_value():
    v = SchemaValidator({'type': 'timedelta'})
    assert v.validate_python('123days, 12:34') == timedelta(days=123, hours=12, minutes=34)
    assert v.validate_python(f'{999_999_999}days, 12:34') == timedelta(days=999_999_999, hours=12, minutes=34)
    with pytest.raises(ValidationError, match='should be a valid timedelta, durations may not exceed 999,999,999 days'):
        v.validate_python(f'{999_999_999 + 1}days, 12:34')


@pytest.mark.skipif(not pandas, reason='pandas not installed')
def test_pandas():
    v = SchemaValidator({'type': 'timedelta', 'ge': timedelta(hours=2)})
    two_hours = pandas.Timestamp('2023-01-01T02:00:00Z') - pandas.Timestamp('2023-01-01T00:00:00Z')

    assert v.validate_python(two_hours) == two_hours
    assert v.validate_python(two_hours.to_pytimedelta()) == two_hours

    one_55 = pandas.Timestamp('2023-01-01T01:55:00Z') - pandas.Timestamp('2023-01-01T00:00:00Z')
    msg = r'Input should be greater than or equal to 2 hours'
    with pytest.raises(ValidationError, match=msg):
        v.validate_python(one_55)
    with pytest.raises(ValidationError, match=msg):
        v.validate_python(one_55.to_pytimedelta())
