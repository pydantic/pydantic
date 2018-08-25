from datetime import datetime, timedelta
from pydantic import BaseModel
from pydantic.json import timedelta_isoformat

class BarModel(BaseModel):
    whatever: int

class FooBarModel(BaseModel):
    banana: float
    foo: datetime
    bar: BarModel

m = FooBarModel(banana=3.14, foo=datetime(2032, 6, 1, 12, 13, 14), bar={'whatever': 123})

print(m.json())
# (returns a str)
# > {"banana": 3.14, "foo": "2032-06-01T12:13:14", "bar": {"whatever": 123}}

class WithCustomEncoders(BaseModel):
    dt: datetime
    diff: timedelta

    class Config:
        json_encoders = {
            datetime: lambda v: (v - datetime(1970, 1, 1)).total_seconds(),
            timedelta: timedelta_isoformat,
        }

print(WithCustomEncoders(dt=datetime(2032, 6, 1, microsecond=500000), diff=timedelta(hours=100)).json())
# > {"dt": 1969660800.5, "diff": "P4DT4H0M0.000000S"}
