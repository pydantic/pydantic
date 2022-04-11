from datetime import date, datetime

import pytest

from pydantic import BaseModel, ValidationError, condate

base_message = r'.*ensure this value is {msg} \(type=value_error.number.not_{ty}; limit_value={value}\).*'


def test_date_gt():
    threshold = date(2020, 1, 1)

    class Model(BaseModel):
        a: condate(gt=threshold)

    assert Model(a=date(2020, 1, 2)).dict() == {'a': date(2020, 1, 2)}

    message = base_message.format(msg=f'greater than {threshold}', ty='gt', value=threshold)
    with pytest.raises(ValidationError, match=message):
        Model(a=date(2019, 1, 1))


def test_date_ge():
    threshold = date(2020, 1, 1)

    class Model(BaseModel):
        a: condate(ge=threshold)

    assert Model(a=date(2020, 1, 1)).dict() == {'a': date(2020, 1, 1)}

    message = base_message.format(msg=f'greater than or equal to {threshold}', ty='ge', value=threshold)
    with pytest.raises(ValidationError, match=message):
        Model(a=date(2019, 1, 1))


def test_date_lt():
    threshold = date(2020, 1, 1)

    class Model(BaseModel):
        a: condate(lt=threshold)

    assert Model(a=date(2019, 1, 2)).dict() == {'a': date(2019, 1, 2)}

    message = base_message.format(msg=f'less than {threshold}', ty='lt', value=threshold)
    with pytest.raises(ValidationError, match=message):
        Model(a=date(2021, 1, 1))


def test_date_le():
    threshold = date(2020, 1, 1)

    class Model(BaseModel):
        a: condate(le=threshold)

    assert Model(a=date(2019, 1, 1)).dict() == {'a': date(2019, 1, 1)}

    message = base_message.format(msg=f'less than or equal to {threshold}', ty='le', value=threshold)
    with pytest.raises(ValidationError, match=message):
        Model(a=date(2021, 1, 1))


def test_date_strict_formats():
    class Model(BaseModel):
        a: condate(strict_formats=['%Y-%m-%d', '%d %b %Y'])  # noqa: F722

    assert Model(a=date(2020, 1, 1)).dict() == {'a': date(2020, 1, 1)}
    assert Model(a=datetime(2020, 1, 1)).dict() == {'a': date(2020, 1, 1)}
    assert Model(a='2020-01-01').dict() == {'a': date(2020, 1, 1)}
    assert Model(a='1 Jan 2020').dict() == {'a': date(2020, 1, 1)}

    with pytest.raises(ValidationError, match='invalid date format'):
        Model(a=100)  # without strict format this would be interpreted as seconds since 1970

    with pytest.raises(ValidationError, match='invalid date format'):
        Model(a=1981)  # without strict format this would be interpreted as datetime.date(1981, 1, 1)
