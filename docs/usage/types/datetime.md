---
description: Support for datetime types.
---

Pydantic supports the following [datetime](https://docs.python.org/library/datetime.html#available-types)
types:

* `datetime.date`
* `datetime.time`
* `datetime.datetime`
* `datetime.timedelta`

## Validation of datetime types

* `datetime` fields will accept values of type:

    * `datetime`; an existing `datetime` object
    * `int` or `float`; assumed as Unix time, i.e. seconds (if >= `-2e10` and <= `2e10`) or milliseconds
      (if < `-2e10`or > `2e10`) since 1 January 1970
    * `str`; the following formats are accepted:
        * `YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]`
        * `int` or `float` as a string (assumed as Unix time)

* `date` fields will accept values of type:

    * `date`; an existing `date` object
    * `int` or `float`; handled the same as described for `datetime` above
    * `str`; the following formats are accepted:
        * `YYYY-MM-DD`
        * `int` or `float` as a string (assumed as Unix time)

* `time` fields will accept values of type:

    * `time`; an existing `time` object
    * `str`; the following formats are accepted:
        * `HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]`

* `timedelta` fields will accept values of type:

    * `timedelta`; an existing `timedelta` object
    * `int` or `float`; assumed to be seconds
    * `str`; the following formats are accepted:
        * `[-][DD ][HH:MM]SS[.ffffff]`
        * `[±]P[DD]DT[HH]H[MM]M[SS]S` ([ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format for timedelta)

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

## Pydantic date types

The following types can be imported from `pydantic`, and augment the types described above
with additional validation constraints:

`PastDate`
: like `date`, with the constraint that the value must be in the past

`FutureDate`
: like `date`, with the constraint that the value must be in the future

`PastDatetime`
: like `PastDate`, but for `datetime`

`FutureDatetime`
: like `FutureDate`, but for `datetime`

`AwareDatetime`
: like `datetime`, with the constraint that the value must have timezone info

`NaiveDatetime`
: like `datetime`, with the constraint that the value must lack timezone info
