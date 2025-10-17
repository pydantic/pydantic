Native Pendulum DateTime object implementation. This is a copy of the Pendulum DateTime object, but with a Pydantic CoreSchema implementation. This allows Pydantic to validate the DateTime object.

## DateTime

Bases: `DateTime`

A `pendulum.DateTime` object. At runtime, this type decomposes into pendulum.DateTime automatically. This type exists because Pydantic throws a fit on unknown types.

```python
from pydantic import BaseModel
from pydantic_extra_types.pendulum_dt import DateTime


class test_model(BaseModel):
    dt: DateTime


print(test_model(dt='2021-01-01T00:00:00+00:00'))

# > test_model(dt=DateTime(2021, 1, 1, 0, 0, 0, tzinfo=FixedTimezone(0, name="+00:00")))

```

## Time

Bases: `Time`

A `pendulum.Time` object. At runtime, this type decomposes into pendulum.Time automatically. This type exists because Pydantic throws a fit on unknown types.

```python
from pydantic import BaseModel
from pydantic_extra_types.pendulum_dt import Time


class test_model(BaseModel):
    dt: Time


print(test_model(dt='00:00:00'))

# > test_model(dt=Time(0, 0, 0))

```

## Date

Bases: `Date`

A `pendulum.Date` object. At runtime, this type decomposes into pendulum.Date automatically. This type exists because Pydantic throws a fit on unknown types.

```python
from pydantic import BaseModel
from pydantic_extra_types.pendulum_dt import Date


class test_model(BaseModel):
    dt: Date


print(test_model(dt='2021-01-01'))

# > test_model(dt=Date(2021, 1, 1))

```

## Duration

Bases: `Duration`

A `pendulum.Duration` object. At runtime, this type decomposes into pendulum.Duration automatically. This type exists because Pydantic throws a fit on unknown types.

```python
from pydantic import BaseModel
from pydantic_extra_types.pendulum_dt import Duration


class test_model(BaseModel):
    delta_t: Duration


print(test_model(delta_t='P1DT25H'))

# > test_model(delta_t=Duration(days=2, hours=1))

```

### to_iso8601_string

```python
to_iso8601_string() -> str

```

Convert a Duration object to an ISO 8601 string.

In addition to the standard ISO 8601 format, this method also supports the representation of fractions of a second and negative durations.

Returns:

| Type | Description | | --- | --- | | `str` | The ISO 8601 string representation of the duration. |

Source code in `pydantic_extra_types/pendulum_dt.py`

```python
def to_iso8601_string(self) -> str:
    """
    Convert a Duration object to an ISO 8601 string.

    In addition to the standard ISO 8601 format, this method also supports the representation of fractions of a second and negative durations.

    Returns:
        The ISO 8601 string representation of the duration.
    """
    # Extracting components from the Duration object
    years = self.years
    months = self.months
    days = self._days
    hours = self.hours
    minutes = self.minutes
    seconds = self.remaining_seconds
    milliseconds = self.microseconds // 1000
    microseconds = self.microseconds % 1000

    # Constructing the ISO 8601 duration string
    iso_duration = 'P'
    if years or months or days:
        if years:
            iso_duration += f'{years}Y'
        if months:
            iso_duration += f'{months}M'
        if days:
            iso_duration += f'{days}D'

    if hours or minutes or seconds or milliseconds or microseconds:
        iso_duration += 'T'
        if hours:
            iso_duration += f'{hours}H'
        if minutes:
            iso_duration += f'{minutes}M'
        if seconds or milliseconds or microseconds:
            iso_duration += f'{seconds}'
            if milliseconds or microseconds:
                iso_duration += f'.{milliseconds:03d}'
            if microseconds:
                iso_duration += f'{microseconds:03d}'
            iso_duration += 'S'

    # Prefix with '-' if the duration is negative
    if self.total_seconds() < 0:
        iso_duration = '-' + iso_duration

    if iso_duration == 'P':
        iso_duration = 'P0D'

    return iso_duration

```
