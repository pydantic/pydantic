from datetime import datetime, timedelta
import pendulum
from pydantic import BaseModel
from pydantic.json import timedelta_isoformat

class BarModel(BaseModel):
    whatever: int

class FooBarModel(BaseModel):
    foo: datetime
    bar: BarModel

m = FooBarModel(foo=datetime(2032, 6, 1, 12, 13, 14), bar={'whatever': 123})
print(m.json())
# (returns a str)
class WithCustomEncoders(BaseModel):
    dt: datetime
    diff: timedelta

    class Config:
        json_encoders = {
            datetime: lambda v: v.timestamp(),
            timedelta: timedelta_isoformat,
        }

m = WithCustomEncoders(dt=datetime(2032, 6, 1), diff=timedelta(hours=100))
print(m.json())
# (returns a str)
class WithSubclasses(BaseModel):
    pdt: pendulum.DateTime
    pdiff: pendulum.Duration

    class Config:
        json_encoders = {
            datetime: lambda v: v.timestamp(),
            timedelta: timedelta_isoformat,
        }

m = WithSubclasses(
    pdt=pendulum.datetime(2032, 6, 1),
    pdiff=pendulum.duration(months=3, days=2, hours=1),
)
print(m.json())
