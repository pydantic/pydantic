from datetime import datetime

from pydantic import validator
from pydantic.dataclasses import dataclass


@dataclass
class DemoDataclass:
    ts: datetime = None

    @validator('ts', pre=True, always=True)
    def set_ts_now(cls, v):
        return v or datetime.now()


print(DemoDataclass())
# > DemoDataclass(ts=datetime.datetime(2019, 4, 2, 18, 1, 46, 66149))

print(DemoDataclass(ts='2017-11-08T14:00'))
# > DemoDataclass ts=datetime.datetime(2017, 11, 8, 14, 0)