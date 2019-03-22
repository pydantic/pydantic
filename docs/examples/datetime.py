from datetime import date, datetime, time, timedelta
from pydantic import BaseModel

class Model(BaseModel):
    date_date: date = None
    date_dt: date = None
    date_int: date = None
    date_float: date = None
    date_str: date = None

    datetime_dt: datetime = None
    datetime_int: datetime = None
    datetime_float: datetime = None
    datetime_str: datetime = None

    time_time: time = None
    time_str: time = None

    timedelta_int: timedelta = None
    timedelta_float: timedelta = None
    timedelta_str: timedelta = None

# date
print(Model(date_date=date(2012, 4, 9)).date_date)  # > 2012-04-09
print(Model(date_dt=datetime(2012, 4, 9, 12, 15)).date_dt)  # > 2012-04-09
# integer or float values <= 2e10 parsed as seconds since 1 January 1970
print(Model(date_int=1_549_316_052).date_int)  # > 2019-02-04
# values greater than 2e10 parsed as milliseconds
print(Model(date_int=1_549_316_052_104).date_int)  # > 2019-02-04
print(Model(date_float=1_549_316_052_104.123456789).date_float)  # > 2019-02-04
# value checked against int() or float()
print(Model(date_str='1_549_316_052_104').date_str)  # > 2019-02-04
# otherwise strings matched against YYYY-MM-DD pattern, i.e. year, month, day
print(Model(date_str='2014-02-04').date_str)  # > 2019-02-04
print(Model(date_str='2014-2-4').date_str)  # > 2019-02-04

# datetime is analogous to date,
# although it has an extended version of the string format:
# YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z[+[-]HH[:]MM]]],
# i.e. year, month, day, hour, minute, second, microsecond, and tzinfo.
print(Model(datetime_str='2012-04-23T09:15:00').datetime_str)  # > 2012-04-23 09:15:00
print(Model(datetime_str='2012-4-9 4:8:16').datetime_str)  # > 2012-04-09 04:08:16
print(Model(datetime_str='2012-04-23T09:15:00Z').datetime_str)  # > 2012-04-23 09:15:00+00:00
print(Model(datetime_str='2012-4-9 4:8:16-0320').datetime_str)  # > 2012-04-09 04:08:16-03:20
print(Model(datetime_str='2012-04-23T10:20:30.400+02:30').datetime_str)  # > 2012-04-23 10:20:30.400000+02:30
print(Model(datetime_str='2012-04-23T10:20:30.400+02').datetime_str)  # > 2012-04-23 10:20:30.400000+02:00
print(Model(datetime_str='2012-04-23T10:20:30.400-02').datetime_str)  # > 2012-04-23 10:20:30.400000-02:00

# time
print(Model(time_time=time(4, 8, 16)).time_time)  # > 4:08:16
# time as string parsed against format
# HH:MM:[SS[.ffffff]], i.e. hour, minute, second, microsecond
print(Model(time_str='10:10').time_str)  # > 10:10:00
print(Model(time_str='10:10:15').time_str)  # > 10:10:15
print(Model(time_str='10:10:15.123456').time_str)  # > 10:10:15.123456

# timedelta
# internally integers and floats converted to strings
print(Model(timedelta_int=15).timedelta_int)  # > 0:00:15
print(Model(timedelta_float=15.17).timedelta_float)  # > 0:00:15.170000
# strings are matched against either of two formats:
# [-][DD ][HH:MM]SS[.ffffff]
# i.e. days, hours, minutes, seconds, and microseconds
print(Model(timedelta_str='-2 15:30.000001').timedelta_str)  # > -2 days, 0:15:30.000001
# or ISO 8601 format: [+-]P[DD]T[HH]H[MM]M[SS]S
print(Model(timedelta_str='P3DT12H30M5S').timedelta_str)  # > 3 days, 12:30:05
