"""
Test mypy failure with missing attribute
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from pydantic.types import Json


class Model(BaseModel):
    age: int
    first_name = 'John'
    last_name: Optional[str] = None
    signup_ts: Optional[datetime] = None
    list_of_ints: List[int]
    json_list_of_ints: Json[List[int]]


m = Model(age=42, list_of_ints=[1, '2', b'3'])

print(m.age + 'not integer')
# MYPY: error: Unsupported operand types for + ("int" and "str")  [operator]
m.json_list_of_ints[0] + 'not integer'
# MYPY: error: Unsupported operand types for + ("int" and "str")  [operator]
