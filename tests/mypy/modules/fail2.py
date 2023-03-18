"""
Test mypy failure with invalid types.
"""
from datetime import datetime

from pydantic import BaseModel


class Model(BaseModel):
    age: int
    first_name = 'John'
    last_name: str | None = None
    signup_ts: datetime | None = None
    list_of_ints: list[int]


m = Model(age=42, list_of_ints=[1, '2', b'3'])

print(m.foobar)
