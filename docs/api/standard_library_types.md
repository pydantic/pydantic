---
description: Support for common types from the Python standard library.
---

Pydantic supports many common types from the Python standard library. If you need stricter processing see
[Strict Types](../usage/types/strict_types.md), including if you need to constrain the values allowed (e.g. to require a positive `int`).

## Booleans

A standard `bool` field will raise a `ValidationError` if the value is not one of the following:

* A valid boolean (i.e. `True` or `False`),
* The integers `0` or `1`,
* a `str` which when converted to lower case is one of
  `'0', 'off', 'f', 'false', 'n', 'no', '1', 'on', 't', 'true', 'y', 'yes'`
* a `bytes` which is valid per the previous rule when decoded to `str`

!!! note
    If you want stricter boolean logic (e.g. a field which only permits `True` and `False`) you can
    use [`StrictBool`](../api/types.md#pydantic.types.StrictBool).

Here is a script demonstrating some of these behaviors:

```py
from pydantic import BaseModel, ValidationError


class BooleanModel(BaseModel):
    bool_value: bool


print(BooleanModel(bool_value=False))
#> bool_value=False
print(BooleanModel(bool_value='False'))
#> bool_value=False
print(BooleanModel(bool_value=1))
#> bool_value=True
try:
    BooleanModel(bool_value=[])
except ValidationError as e:
    print(str(e))
    """
    1 validation error for BooleanModel
    bool_value
      Input should be a valid boolean [type=bool_type, input_value=[], input_type=list]
    """
```

## Datetime Types

Pydantic supports the following [datetime](https://docs.python.org/library/datetime.html#available-types)
types:

### `datetime.datetime`
* `datetime` fields will accept values of type:

    * `datetime`; an existing `datetime` object
    * `int` or `float`; assumed as Unix time, i.e. seconds (if >= `-2e10` and <= `2e10`) or milliseconds
      (if < `-2e10`or > `2e10`) since 1 January 1970
    * `str`; the following formats are accepted:
        * `YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]`
        * `int` or `float` as a string (assumed as Unix time)

```py
from datetime import datetime

from pydantic import BaseModel


class Event(BaseModel):
    dt: datetime = None


event = Event(dt='2032-04-23T10:20:30.400+02:30')

print(event.model_dump())
"""
{'dt': datetime.datetime(2032, 4, 23, 10, 20, 30, 400000, tzinfo=TzInfo(+02:30))}
"""
```

### `datetime.date`
* `date` fields will accept values of type:

    * `date`; an existing `date` object
    * `int` or `float`; handled the same as described for `datetime` above
    * `str`; the following formats are accepted:
        * `YYYY-MM-DD`
        * `int` or `float` as a string (assumed as Unix time)

```py
from datetime import date

from pydantic import BaseModel


class Birthday(BaseModel):
    d: date = None


my_birthday = Birthday(d=1679616000.0)

print(my_birthday.model_dump())
#> {'d': datetime.date(2023, 3, 24)}
```

### `datetime.time`
* `time` fields will accept values of type:

    * `time`; an existing `time` object
    * `str`; the following formats are accepted:
        * `HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]`

```py
from datetime import time

from pydantic import BaseModel


class Meeting(BaseModel):
    t: time = None


m = Meeting(t=time(4, 8, 16))

print(m.model_dump())
#> {'t': datetime.time(4, 8, 16)}
```

### `datetime.timdelta`
* `timedelta` fields will accept values of type:

    * `timedelta`; an existing `timedelta` object
    * `int` or `float`; assumed to be seconds
    * `str`; the following formats are accepted:
        * `[-][DD ][HH:MM]SS[.ffffff]`
        * `[±]P[DD]DT[HH]H[MM]M[SS]S` ([ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format for timedelta)

```py
from datetime import timedelta

from pydantic import BaseModel


class Model(BaseModel):
    td: timedelta = None


m = Model(td='P3DT12H30M5S')

print(m.model_dump())
#> {'td': datetime.timedelta(days=3, seconds=45005)}
```

## Number Types

Pydantic supports the following numeric types from the Python standard library:

### `int`

* Pydantic uses `int(v)` to coerce types to an `int`;
  see [Data conversion](../usage/models.md#data-conversion) for details on loss of information during data conversion.

### `float`

* Pydantic uses `float(v)` to coerce values to floats.

### `enum.IntEnum`

* Validation: Pydantic checks that the value is a valid `IntEnum` instance.

#### subclass of `enum.IntEnum`

* Validation: checks that the value is a valid member of the integer enum;
  see [Enums and Choices](../usage/types/enums.md) for more details.


### `decimal.Decimal`

* Validation: Pydantic attempts to convert the value to a string, then passes the string to `Decimal(v)`.
* Serialization: Pydantic serializes `Decimal` types as strings.
You can use a custom serializer to override this behavior if desired. For example:

```py
from decimal import Decimal

from typing_extensions import Annotated

from pydantic import BaseModel, PlainSerializer


class Model(BaseModel):
    x: Decimal
    y: Annotated[
        Decimal,
        PlainSerializer(
            lambda x: float(x), return_type=float, when_used='json'
        ),
    ]


my_model = Model(x=Decimal('1.1'), y=Decimal('2.1'))

print(my_model.model_dump())  # (1)!
#> {'x': Decimal('1.1'), 'y': Decimal('2.1')}
print(my_model.model_dump(mode='json'))  # (2)!
#> {'x': '1.1', 'y': 2.1}
print(my_model.model_dump_json())  # (3)!
#> {"x":"1.1","y":2.1}
```

1. Using [`model_dump`][pydantic.main.model_dump], both `x` and `y` remain instances of the `Decimal` type
2. Using [`model_dump`][pydantic.main.model_dump] with `mode='json'`, `x` is serialized as a `string`, and `y` is serialized as a `float` because of the custom serializer applied.
3. Using [`model_dump_json`][pydantic.main.model_dump_json], `x` is serialized as a `string`, and `y` is serialized as a `float` because of the custom serializer applied.
