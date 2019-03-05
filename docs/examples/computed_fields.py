from datetime import date

from pydantic import BaseModel, Schema

def to_date(values, raw):
    return date(**values)
    

class Foo(BaseModel):
    day: int
    month: int
    year: int
    created_at: date = Schema(..., compute=to_date)


m = Foo(day=1, month=1, year=2019)
print(m)
# Foo day=1 month=1 year=2019 created_at=datetime.date(2019, 1, 1)