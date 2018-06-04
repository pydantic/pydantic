from typing import List

from pydantic import BaseModel, ValidationError, conint


class Location(BaseModel):
    lat = 0.1
    lng = 10.1


class Model(BaseModel):
    list_of_ints: List[int] = None
    a_float: float = None
    is_required: float = ...
    recursive_model: Location = None
    gt_int: conint(gt=42) = ...


try:
    Model(
        list_of_ints=['1', 2, 'bad'],
        a_float='not a float',
        recursive_model={'lat': 4.2, 'lng': 'New York'},
        gt_int=21
    )
except ValidationError as e:
    print(e)

"""
validation errors
list_of_ints -> 2
  value is not a valid integer (type=type_error.integer)
a_float
  value is not a valid float (type=type_error.float)
is_required
  field required (type=value_error.missing)
recursive_model -> lng
  value is not a valid float (type=type_error.float)
gt_int
  ensure this value is greater than 42 (type=value_error.number.gt; limit_value=42)
"""

try:
    Model(list_of_ints=1, a_float=None, recursive_model=[1, 2, 3], gt_int=21)
except ValidationError as e:
    print(e.json())

"""
[
  {
    "loc": [
      "list_of_ints"
    ],
    "msg": "value is not a valid sequence",
    "type": "type_error.sequence"
  },
  {
    "loc": [
      "is_required"
    ],
    "msg": "field required",
    "type": "value_error.missing"
  },
  {
    "loc": [
      "recursive_model"
    ],
    "msg": "value is not a valid dict",
    "type": "type_error.dict"
  },
  {
    "ctx": {
      "limit_value": 42
    },
    "loc": [
      "gt_int"
    ],
    "msg": "ensure this value is greater than 42",
    "type": "value_error.number.gt"
  }
]
"""
