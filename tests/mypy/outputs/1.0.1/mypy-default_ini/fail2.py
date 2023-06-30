"""
Test mypy failure with invalid types.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Model(BaseModel):
    age: int
    first_name = 'John'
    last_name: Optional[str] = None
    signup_ts: Optional[datetime] = None
    list_of_ints: List[int]


m = Model(age=42, list_of_ints=[1, '2', b'3'])

print(m.foobar)
# MYPY: error: "Model" has no attribute "foobar"  [attr-defined]
