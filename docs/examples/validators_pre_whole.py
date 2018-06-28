import json
from typing import List

from pydantic import BaseModel, ValidationError, validator


class DemoModel(BaseModel):
    numbers: List[int] = []
    people: List[str] = []

    @validator('people', 'numbers', pre=True, whole=True)
    def json_decode(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except ValueError:
                pass
        return v

    @validator('numbers')
    def check_numbers_low(cls, v):
        if v > 4:
            raise ValueError(f'number too large {v} > 4')
        return v

    @validator('numbers', whole=True)
    def check_sum_numbers_low(cls, v):
        if sum(v) > 8:
            raise ValueError(f'sum of numbers greater than 8')
        return v


print(DemoModel(numbers='[1, 1, 2, 2]'))
# > DemoModel numbers=[1, 1, 2, 2] people=[]

try:
    DemoModel(numbers='[1, 2, 5]')
except ValidationError as e:
    print(e)
"""
1 validation error
numbers -> 2
  number too large 5 > 4 (type=value_error)
"""

try:
    DemoModel(numbers=[3, 3, 3])
except ValidationError as e:
    print(e)
"""
1 validation error
numbers
  sum of numbers greater than 8 (type=value_error)
"""
