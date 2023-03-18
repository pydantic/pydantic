"""
Test mypy failure with missing attribute
"""
from datetime import datetime

from pydantic import BaseModel
from pydantic.types import Json


class Model(BaseModel):
    age: int
    first_name = 'John'
    last_name: str | None = None
    signup_ts: datetime | None = None
    list_of_ints: list[int]
    json_list_of_ints: Json[list[int]]


m = Model(age=42, list_of_ints=[1, '2', b'3'])

print(m.age + 'not integer')
m.json_list_of_ints[0] + 'not integer'
