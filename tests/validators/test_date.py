from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from pydantic_core import SchemaError, SchemaValidator, ValidationError, core_schema
from pydantic_core import core_schema as cs

from ..conftest import Err, PyAndJson


@pytest.mark.parametrize(
    'constraint',
    ['le', 'lt', 'ge', 'gt'],
)
def test_constraints_schema_validation_error(constraint: str) -> None:
    with pytest.raises(SchemaError, match=f"'{constraint}' must be coercible to a date instance"):
        SchemaValidator(cs.date_schema(**{constraint: 'bad_value'}))


def test_constraints_schema_validation() -> None:
    val = SchemaValidator(cs.date_schema(gt='2020-01-01'))
    with pytest.raises(ValidationError):
        val.validate_python('2019-01-01')


@pytest.mark.parametrize(
    'input_value,expected',
    [
        pytest.param(date(2022, 6, 8), date(2022, 6, 8), id='date'),
        pytest.param('2022-06-08', date(2022, 6, 8), id='str'),
        pytest.param(b'2022-06-08', date(2022, 6, 8), id='bytes'),
        pytest.param((1,), Err('Input should be a valid date [type=date_type'), id='tuple'),
        pytest.param(1654646400, date(2022, 6, 8), id='int'),
        pytest.param('1654646400', date(2022, 6, 8), id='int-as-str'),
        pytest.param(1654646400.00, date(2022, 6, 8), id='float'),
        pytest.param('1654646400.00', date(2022, 6, 8), id='float-as-str'),
        pytest.param(Decimal('1654646400'), date(2022, 6, 8), id='decimal'),
        pytest.param(253_402_300_800_000, Err('Input should be a valid date'), id='int-too-high'),
        pytest.param(-80_000_000_000_000, Err('Input should be a valid date'), id='int-too-low'),
        pytest.param(datetime(2022, 6, 8), date(2022, 6, 8), id='datetime-exact'),
        pytest.param(
            datetime(2022, 6, 8, 12),
            Err(
                'Datetimes provided to dates should have zero time '
                '- e.g. be exact dates [type=date_from_datetime_inexact'
            ),
            id='datetime-inexact',
        ),
        pytest.param(1654646400 + 4, Err('type=date_from_datetime_inexact'), id='int-inexact'),
        pytest.param(1654646400.1, Err('type=date_from_datetime_inexact'), id='float-inexact'),
        pytest.param('1654646404', Err('type=date_from_datetime_inexact'), id='int-str-inexact'),
        pytest.param('1654646400.1', Err('type=date_from_datetime_inexact'), id='float-str-inexact'),
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
                'Input should be a valid date or datetime, dates before 0000 are not supported as unix timestamps '
                '[type=date_from_datetime_parsing,'
            ),
            id='-inf',
        ),
        pytest.param('-', Err('Input should be a valid date or datetime, input is too short'), id='minus'),
        pytest.param('+', Err('Input should be a valid date or datetime, input is too short'), id='pus'),
        pytest.param('0001-01-01', date(1, 1, 1), id='min-date'),
        pytest.param(
            '0000-12-31',
            Err('Input should be a valid date in the format YYYY-MM-DD, year 0 is out of range [type=date_parsing,'),
            id='year-0',
        ),
    ],
)
def test_date(input_value, expected):
    v = SchemaValidator(cs.date_schema())
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            result = v.validate_python(input_value)
            print(f'input_value={input_value!r} result={result}')
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
def test_date_strict(input_value, expected, strict_mode_type):
    v = SchemaValidator(cs.date_schema(strict=strict_mode_type.schema))
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value, **strict_mode_type.validator_args)
    else:
        output = v.validate_python(input_value, **strict_mode_type.validator_args)
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
def test_date_strict_json(input_value, expected, strict_mode_type):
    v = SchemaValidator(cs.date_schema(strict=strict_mode_type.schema))
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_json(input_value, **strict_mode_type.validator_args)
    else:
        output = v.validate_json(input_value, **strict_mode_type.validator_args)
        assert output == expected


def test_date_strict_json_ctx():
    v = SchemaValidator(cs.date_schema(strict=True))
    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('"foobar"')
    assert exc_info.value.errors(include_url=False) == [
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
        ({'lt': date(2000, 1, 1)}, '1999-12-31', date(1999, 12, 31)),
        ({'lt': date(2000, 1, 1)}, '2000-01-01', Err('Input should be less than 2000-01-01 [type=less_than,')),
        ({'ge': date(2000, 1, 1)}, '2000-01-01', date(2000, 1, 1)),
        (
            {'ge': date(2000, 1, 1)},
            '1999-12-31',
            Err('Input should be greater than or equal to 2000-01-01 [type=greater_than_equal,'),
        ),
        ({'gt': date(2000, 1, 1)}, '2000-01-02', date(2000, 1, 2)),
        ({'gt': date(2000, 1, 1)}, '2000-01-01', Err('Input should be greater than 2000-01-01 [type=greater_than,')),
    ],
)
def test_date_kwargs(kwargs: dict[str, Any], input_value: date, expected: Err | date):
    v = SchemaValidator(cs.date_schema(**kwargs))  # type: ignore
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected


def test_dict_py():
    v = SchemaValidator(cs.dict_schema(keys_schema=cs.date_schema(), values_schema=cs.int_schema()))
    assert v.validate_python({date(2000, 1, 1): 2, date(2000, 1, 2): 4}) == {date(2000, 1, 1): 2, date(2000, 1, 2): 4}


def test_dict(py_and_json: PyAndJson):
    v = py_and_json({'type': 'dict', 'keys_schema': {'type': 'date'}, 'values_schema': {'type': 'int'}})
    assert v.validate_test({'2000-01-01': 2, '2000-01-02': 4}) == {date(2000, 1, 1): 2, date(2000, 1, 2): 4}


def test_union():
    v = SchemaValidator(cs.union_schema(choices=[cs.str_schema(), cs.date_schema()]))
    assert v.validate_python('2022-01-02') == '2022-01-02'
    assert v.validate_python(date(2022, 1, 2)) == date(2022, 1, 2)

    v = SchemaValidator(cs.union_schema(choices=[cs.date_schema(), cs.str_schema()]))
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
    today = datetime.now(timezone.utc).date()
    assert v.isinstance_python(today) is False
    assert v.isinstance_python(today - timedelta(days=1)) is True
    assert v.isinstance_python(today + timedelta(days=1)) is False

    v = SchemaValidator(core_schema.date_schema(now_op='future', now_utc_offset=0))
    assert v.isinstance_python(today) is False
    assert v.isinstance_python(today - timedelta(days=1)) is False
    assert v.isinstance_python(today + timedelta(days=1)) is True


@pytest.mark.parametrize(
    'val_temporal_unit, input_value, expected',
    [
        # 'seconds' mode: treat as seconds since epoch
        ('seconds', 1654646400, date(2022, 6, 8)),
        ('seconds', '1654646400', date(2022, 6, 8)),
        ('seconds', 1654646400.0, date(2022, 6, 8)),
        ('seconds', 8640000000.0, date(2243, 10, 17)),
        ('seconds', 92534400000.0, date(4902, 4, 20)),
        # 'milliseconds' mode: treat as milliseconds since epoch
        ('milliseconds', 1654646400000, date(2022, 6, 8)),
        ('milliseconds', '1654646400000', date(2022, 6, 8)),
        ('milliseconds', 1654646400000.0, date(2022, 6, 8)),
        ('milliseconds', 8640000000.0, date(1970, 4, 11)),
        ('milliseconds', 92534400000.0, date(1972, 12, 7)),
        # 'infer' mode: large numbers are ms, small are s
        ('infer', 1654646400, date(2022, 6, 8)),
        ('infer', 1654646400000, date(2022, 6, 8)),
        ('infer', 8640000000.0, date(2243, 10, 17)),
        ('infer', 92534400000.0, date(1972, 12, 7)),
    ],
)
def test_val_temporal_unit_date(val_temporal_unit, input_value, expected):
    v = SchemaValidator(
        cs.date_schema(),
        config={'val_temporal_unit': val_temporal_unit},
    )
    output = v.validate_python(input_value)
    assert output == expected
