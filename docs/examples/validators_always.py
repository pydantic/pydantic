from datetime import datetime

from pydantic import BaseModel, validator


class DemoModel(BaseModel):
    ts: datetime = None

    @validator('ts', pre=True, always=True)
    def set_ts_now(cls, v):
        return v or datetime.now()


print(DemoModel())
#> DemoModel ts=datetime.datetime(2017, 11, 8, 13, 59, 11, 723629)

print(DemoModel(ts='2017-11-08T14:00'))
#> DemoModel ts=datetime.datetime(2017, 11, 8, 14, 0)
