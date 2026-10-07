Time zone name validation and serialization module.

## TimeZoneName

Bases: `str`

TimeZoneName is a custom string subclass for validating and serializing timezone names.

The TimeZoneName class uses the IANA Time Zone Database for validation. It supports both strict and non-strict modes for timezone name validation.

#### Examples:

Some examples of using the TimeZoneName class:

##### Normal usage:

```python
from pydantic_extra_types.timezone_name import TimeZoneName
from pydantic import BaseModel
class Location(BaseModel):
    city: str
    timezone: TimeZoneName

loc = Location(city="New York", timezone="America/New_York")
print(loc.timezone)

>> America/New_York

```

##### Non-strict mode:

```python
from pydantic_extra_types.timezone_name import TimeZoneName, timezone_name_settings

@timezone_name_settings(strict=False)
class TZNonStrict(TimeZoneName):
    pass

tz = TZNonStrict("america/new_york")

print(tz)

>> america/new_york

```

## get_timezones

```python
get_timezones() -> set[str]

```

Determine the timezone provider and return available timezones.

Source code in `pydantic_extra_types/timezone_name.py`

```python
def get_timezones() -> set[str]:
    """Determine the timezone provider and return available timezones."""
    if _is_available('zoneinfo'):  # pragma: no cover
        timezones = _tz_provider_from_zone_info()
        if len(timezones) == 0:  # pragma: no cover
            raise ImportError('No timezone provider found. Please install tzdata with "pip install tzdata"')
        return timezones
    elif _is_available('pytz'):  # pragma: no cover
        return _tz_provider_from_pytz()
    else:  # pragma: no cover
        if sys.version_info[:2] == (3, 8):
            raise ImportError('No pytz module found. Please install it with "pip install pytz"')
        raise ImportError('No timezone provider found. Please install tzdata with "pip install tzdata"')

```
