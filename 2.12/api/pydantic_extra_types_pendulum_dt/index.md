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

#> test_model(dt=DateTime(2021, 1, 1, 0, 0, 0, tzinfo=FixedTimezone(0, name="+00:00")))

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

#> test_model(dt=Date(2021, 1, 1))

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

#> test_model(delta_t=Duration(days=2, hours=1))

```
