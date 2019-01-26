"""
Test mypy failure with invalid types.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, NoneStr


class Model(BaseModel):
    age: int
    first_name = 'John'
    last_name: NoneStr = None
    signup_ts: Optional[datetime] = None
    list_of_ints: List[int]


m = Model(age=42, list_of_ints=[1, '2', b'3'])

assert m.age == 42, m.age
print(m.age + 'not integer')
print(m.foobar)
