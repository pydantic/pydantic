from datetime import datetime, timedelta
from pydantic import BaseModel
from pydantic.json import timedelta_isoformat


class BaseClassWithEncoders(BaseModel):
    dt: datetime
    diff: timedelta

    class Config:
        json_encoders = {
            datetime: lambda v: v.timestamp()
        }


class ChildClassWithEncoders(BaseClassWithEncoders):
    class Config:
        json_encoders = {
            timedelta: timedelta_isoformat
        }


m = ChildClassWithEncoders(dt=datetime(2032, 6, 1), diff=timedelta(hours=100))
print(m.json())
