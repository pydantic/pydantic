from typing import List

from pydantic import BaseModel, Json, ValidationError

class SimpleJsonModel(BaseModel):
    json_obj: Json

class ComplexJsonModel(BaseModel):
    json_obj: Json[List[int]]

print(SimpleJsonModel(json_obj='{"b": 1}'))
# > SimpleJsonModel json_obj={'b': 1}

print(ComplexJsonModel(json_obj='[1, 2, 3]'))
# > ComplexJsonModel json_obj=[1, 2, 3]


try:
    ComplexJsonModel(json_obj=12)
except ValidationError as e:
    print(e)
"""
1 validation error
json_obj
  JSON object must be str, bytes or bytearray (type=type_error.json)
"""

try:
    ComplexJsonModel(json_obj='[a, b]')
except ValidationError as e:
    print(e)
"""
1 validation error
json_obj
  Invalid JSON (type=value_error.json)
"""

try:
    ComplexJsonModel(json_obj='["a", "b"]')
except ValidationError as e:
    print(e)
"""
2 validation errors
json_obj -> 0
  value is not a valid integer (type=type_error.integer)
json_obj -> 1
  value is not a valid integer (type=type_error.integer)
"""
