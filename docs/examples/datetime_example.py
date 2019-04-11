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
    td='P3DT12H30M5S'
)

print(m.dict())
# > {'d': datetime.date(2032, 4, 22),
# 'dt': datetime.datetime(2032, 4, 23, 10, 20, 30, 400000, tzinfo=datetime.timezone(datetime.timedelta(seconds=9000))),
# 't': datetime.time(4, 8, 16),
# 'td': datetime.timedelta(days=3, seconds=45005)}
