from datetime import date, datetime, time, timedelta
from pydantic import BaseModel


class Model(BaseModel):
    d: date = None
    dt: datetime = None
    t: time = None
    td: timedelta = None


m = Model(
    d=1966280412345.6789,
    dt='2032-04-23T10:20:30.400+02:30',
    t=time(4, 8, 16),
    td='P3DT12H30M5S',
)

print(m.dict())
