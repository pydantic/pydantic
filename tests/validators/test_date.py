import re
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema

from ..conftest import Err, PyAndJson


@pytest.mark.parametrize(
    'input_value,expected',
    [
        pytest.param(date(2022, 6, 8), date(2022, 6, 8), id='date'),
        pytest.param('2022-06-08', date(2022, 6, 8), id='str'),
        pytest.param(b'2022-06-08', date(2022, 6, 8), id='bytes'),
        pytest.param((1,), Err('Input should be a valid date [type=date_type'), id='tuple'),
        pytest.param(1654646400, date(2022, 6, 8), id='int'),
        pytest.param(1654646400.00, date(2022, 6, 8), id='float'),
        pytest.param(Decimal('1654646400'), date(2022, 6, 8), id='decimal'),
        # (253_402_300_800_000, Err('format YYYY-MM-DD, dates after 9999 are not supported as unix timestamps')),
        pytest.param(253_402_300_800_000, Err('Input should be a valid date'), id='int-too-high'),
        # (-20_000_000_000, Err('format YYYY-MM-DD, dates before 1600 are not supported as unix timestamps')),
        pytest.param(-20_000_000_000, Err('Input should be a valid date'), id='int-too-low'),
        pytest.param(datetime(2022, 6, 8), date(2022, 6, 8), id='datetime-exact'),
        pytest.param(
            datetime(2022, 6, 8, 12),
            Err(
                'Datetimes provided to dates should have zero time '
                '- e.g. be exact dates [type=date_from_datetime_inexact'
            ),
            id='datetime-inexact',
        ),
        pytest.param(True, Err('Input should be a valid date'), id='bool'),
        pytest.param(time(1, 2, 3), Err('Input should be a valid date [type=date_type'), id='time'),
        pytest.param(
            float('nan'),
            Err('Input should be a valid date or datetime, NaN values not permitted [type=date_from_datetime_parsing,'),
            id='nan',
        ),
        pytest.param(
            float('inf'),
            Err(
                'Input should be a valid date or datetime, dates after 9999 are not supported as unix timestamps '
                '[type=date_from_datetime_parsing,'
            ),
            id='inf',
        ),
        pytest.param(
            float('-inf'),
            Err(
                'Input should be a valid date or datetime, dates before 1600 are not supported as unix timestamps '
                '[type=date_from_datetime_parsing,'
            ),
            id='-inf',
        ),
    ],
)
def test_date(input_value, expected):
    v = SchemaValidator({'type': 'date'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            result = v.validate_python(input_value)
            print(f'input_value={input_value} result={result}')
        assert v.isinstance_python(input_value) is False
    else:
        output = v.validate_python(input_value)
        assert output == expected
        assert v.isinstance_python(input_value) is True


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('2022-06-08', date(2022, 6, 8)),
        ('1453-01-28', date(1453, 1, 28)),
        (1654646400, date(2022, 6, 8)),
        (1654646400.0, date(2022, 6, 8)),
        (
            1654646401,
            Err(
                'Datetimes provided to dates should have zero time '
                '- e.g. be exact dates [type=date_from_datetime_inexact'
            ),
        ),
        ('wrong', Err('Input should be a valid date or datetime, input is too short [type=date_from_datetime_parsing')),
        ('2000-02-29', date(2000, 2, 29)),
        (
            '2001-02-29',
            Err(
                'Input should be a valid date or datetime, '
                'day value is outside expected range [type=date_from_datetime_parsing'
            ),
        ),
        ([1], Err('Input should be a valid date [type=date_type')),
    ],
)
def test_date_json(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'date'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
        assert v.isinstance_test(input_value) is False
    else:
        output = v.validate_test(input_value)
        assert output == expected
        assert v.isinstance_test(input_value) is True


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (date(2022, 6, 8), date(2022, 6, 8)),
        ('2022-06-08', Err('Input should be a valid date [type=date_type')),
        (b'2022-06-08', Err('Input should be a valid date [type=date_type')),
        (1654646400, Err('Input should be a valid date [type=date_type')),
        (True, Err('Input should be a valid date [type=date_type')),
        (datetime(2022, 6, 8), Err('Input should be a valid date [type=date_type')),
    ],
    ids=repr,
)
def test_date_strict(input_value, expected):
    v = SchemaValidator({'type': 'date', 'strict': True})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('"2022-06-08"', date(2022, 6, 8)),
        (
            '"foobar"',
            Err('Input should be a valid date in the format YYYY-MM-DD, input is too short [type=date_parsing,'),
        ),
        ('1654646400', Err('Input should be a valid date [type=date_type')),
    ],
)
def test_date_strict_json(input_value, expected):
    v = SchemaValidator({'type': 'date', 'strict': True})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_json(input_value)
    else:
        output = v.validate_json(input_value)
        assert output == expected


def test_date_strict_json_ctx():
    v = SchemaValidator({'type': 'date', 'strict': True})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('"foobar"')
    assert exc_info.value.errors() == [
        {
            'type': 'date_parsing',
            'loc': (),
            'msg': 'Input should be a valid date in the format YYYY-MM-DD, input is too short',
            'input': 'foobar',
            'ctx': {'error': 'input is too short'},
        }
    ]


@pytest.mark.parametrize(
    'kwargs,input_value,expected',
    [
        ({}, '2000-01-01', date(2000, 1, 1)),
        ({'le': date(2000, 1, 1)}, '2000-01-01', date(2000, 1, 1)),
        (
            {'le': date(2000, 1, 1)},
            '2000-01-02',
            Err('Input should be less than or equal to 2000-01-01 [type=less_than_equal,'),
        ),
        ({'lt': '2000-01-01'}, '1999-12-31', date(1999, 12, 31)),
        ({'lt': '2000-01-01'}, '2000-01-01', Err('Input should be less than 2000-01-01 [type=less_than,')),
        ({'ge': '2000-01-01'}, '2000-01-01', date(2000, 1, 1)),
        (
            {'ge': date(2000, 1, 1)},
            '1999-12-31',
            Err('Input should be greater than or equal to 2000-01-01 [type=greater_than_equal,'),
        ),
        ({'gt': date(2000, 1, 1)}, '2000-01-02', date(2000, 1, 2)),
        ({'gt': date(2000, 1, 1)}, '2000-01-01', Err('Input should be greater than 2000-01-01 [type=greater_than,')),
    ],
)
def test_date_kwargs(kwargs: Dict[str, Any], input_value, expected):
    v = SchemaValidator({'type': 'date', **kwargs})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected


def test_invalid_constraint():
    with pytest.raises(SchemaError, match='date -> gt\n  Input should be a valid date or datetime'):
        SchemaValidator({'type': 'date', 'gt': 'foobar'})


def test_dict_py():
    v = SchemaValidator({'type': 'dict', 'keys_schema': {'type': 'date'}, 'values_schema': {'type': 'int'}})
    assert v.validate_python({date(2000, 1, 1): 2, date(2000, 1, 2): 4}) == {date(2000, 1, 1): 2, date(2000, 1, 2): 4}


def test_dict(py_and_json: PyAndJson):
    v = py_and_json({'type': 'dict', 'keys_schema': {'type': 'date'}, 'values_schema': {'type': 'int'}})
    assert v.validate_test({'2000-01-01': 2, '2000-01-02': 4}) == {date(2000, 1, 1): 2, date(2000, 1, 2): 4}


def test_union():
    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'str'}, {'type': 'date'}]})
    assert v.validate_python('2022-01-02') == '2022-01-02'
    assert v.validate_python(date(2022, 1, 2)) == date(2022, 1, 2)

    v = SchemaValidator({'type': 'union', 'choices': [{'type': 'date'}, {'type': 'str'}]})
    assert v.validate_python('2022-01-02') == '2022-01-02'
    assert v.validate_python(date(2022, 1, 2)) == date(2022, 1, 2)


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('2022-06-08', date(2022, 6, 8)),
        (1654646400, date(2022, 6, 8)),
        ('2068-06-08', Err('Date should be in the past [type=date_past,')),
        (3105734400, Err('Date should be in the past [type=date_past,')),
    ],
)
def test_date_past(py_and_json: PyAndJson, input_value, expected):
    # now_utc_offset must be set for all these tests to allow mocking in test_datetime.py!
    v = py_and_json(core_schema.date_schema(now_op='past', now_utc_offset=0))
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
        assert v.isinstance_test(input_value) is False
    else:
        output = v.validate_test(input_value)
        assert output == expected
        assert v.isinstance_test(input_value) is True


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('2022-06-08', Err('Date should be in the future [type=date_future,')),
        (1654646400, Err('Date should be in the future [type=date_future,')),
        ('2068-06-08', date(2068, 6, 8)),
        (3105734400, date(2068, 6, 1)),
    ],
)
def test_date_future(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(core_schema.date_schema(now_op='future', now_utc_offset=0))
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value)
        assert v.isinstance_test(input_value) is False
    else:
        output = v.validate_test(input_value)
        assert output == expected
        assert v.isinstance_test(input_value) is True


def test_date_past_future_today():
    v = SchemaValidator(core_schema.date_schema(now_op='past', now_utc_offset=0))
    today = datetime.utcnow().replace(tzinfo=timezone.utc).date()
    assert v.isinstance_python(today) is False
    assert v.isinstance_python(today - timedelta(days=1)) is True
    assert v.isinstance_python(today + timedelta(days=1)) is False

    v = SchemaValidator(core_schema.date_schema(now_op='future', now_utc_offset=0))
    assert v.isinstance_python(today) is False
    assert v.isinstance_python(today - timedelta(days=1)) is False
    assert v.isinstance_python(today + timedelta(days=1)) is True


def test_offset_too_large():
    with pytest.raises(SchemaError, match=r'Input should be less than 86400 \[type=less_than,'):
        SchemaValidator(core_schema.date_schema(now_op='past', now_utc_offset=24 * 3600))
