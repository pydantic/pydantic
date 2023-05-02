---
description: Support for datetime types.
---

*Pydantic* supports the following [datetime](https://docs.python.org/library/datetime.html#available-types)
types:

`datetime.date`
: see [Datetime Types](#datetime-types) below for more detail on parsing and validation

`datetime.time`
: see [Datetime Types](#datetime-types) below for more detail on parsing and validation

`datetime.datetime`
: see [Datetime Types](#datetime-types) below for more detail on parsing and validation

`datetime.timedelta`
: see [Datetime Types](#datetime-types) below for more detail on parsing and validation

`PastDate`
: like `date`, but the date should be in the past

`FutureDate`
: like `date`, but the date should be in the future

## Datetime types

* `datetime` fields can be:

  * `datetime`, existing `datetime` object
  * `int` or `float`, assumed as Unix time, i.e. seconds (if >= `-2e10` or <= `2e10`) or milliseconds (if < `-2e10`or > `2e10`) since 1 January 1970
  * `str`, following formats work:

    * `YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]`
    * `int` or `float` as a string (assumed as Unix time)

* `date` fields can be:

  * `date`, existing `date` object
  * `int` or `float`, see `datetime`
  * `str`, following formats work:

    * `YYYY-MM-DD`
    * `int` or `float`, see `datetime`

* `time` fields can be:

  * `time`, existing `time` object
  * `str`, following formats work:

    * `HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]`

* `timedelta` fields can be:

  * `timedelta`, existing `timedelta` object
  * `int` or `float`, assumed as seconds
  * `str`, following formats work:

    * `[-][DD ][HH:MM]SS[.ffffff]`
    * `[±]P[DD]DT[HH]H[MM]M[SS]S` ([ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format for timedelta)


## Pydantic date types

`PastDate`
: like `date`, but the date should be in the past

`FutureDate`
: like `date`, but the date should be in the future

`AwareDatetime`
: like `datetime`, but requires the value to have timezone info

`NaiveDatetime`
: like `datetime`, but requires the value to lack timezone info


```py
from datetime import date, datetime, time, timedelta

from pydantic import BaseModel


class Model(BaseModel):
    d: date = None
    dt: datetime = None
    t: time = None
    td: timedelta = None


m = Model(
    d=1679616000.0,
    dt='2032-04-23T10:20:30.400+02:30',
    t=time(4, 8, 16),
    td='P3DT12H30M5S',
)

print(m.model_dump())
"""
{'d': datetime.date(2023, 3, 24), 'dt': datetime.datetime(2032, 4, 23, 10, 20, 30, 400000, tzinfo=TzInfo(+02:30)), 't': datetime.time(4, 8, 16), 'td': datetime.timedelta(days=3, seconds=45005)}
"""
```
