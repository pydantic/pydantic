from datetime import datetime, timedelta
from pydantic import BaseModel
from pydantic.json import timedelta_isoformat


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
