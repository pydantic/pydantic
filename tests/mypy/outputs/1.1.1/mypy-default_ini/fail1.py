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
# MYPY: error: Missing named argument "json_list_of_ints" for "Model"  [call-arg]
# MYPY: error: List item 1 has incompatible type "str"; expected "int"  [list-item]
# MYPY: error: List item 2 has incompatible type "bytes"; expected "int"  [list-item]

print(m.age + 'not integer')
# MYPY: error: Unsupported operand types for + ("int" and "str")  [operator]
m.json_list_of_ints[0] + 'not integer'
# MYPY: error: Unsupported operand types for + ("int" and "str")  [operator]
