from typing import List

from pydantic import BaseModel, ValidationError


class Location(BaseModel):
    lat = 0.1
    lng = 10.1

class Model(BaseModel):
    list_of_ints: List[int] = None
    a_float: float = None
    is_required: float = ...
    recursive_model: Location = None

try:
    Model(list_of_ints=['1', 2, 'bad'], a_float='not a float', recursive_model={'lat': 4.2, 'lng': 'New York'})
except ValidationError as e:
    print(e)

"""
4 errors validating input
list_of_ints:
  invalid literal for int() with base 10: 'bad' (error_type=ValueError track=int index=2)
a_float:
  could not convert string to float: 'not a float' (error_type=ValueError track=float)
is_required:
  field required (error_type=Missing)
recursive_model:
  error validating input (error_type=ValidationError track=Location)
    lng:
      could not convert string to float: 'New York' (error_type=ValueError track=float
"""

try:
    Model(list_of_ints=1, a_float=None, recursive_model=[1, 2, 3])
except ValidationError as e:
    print(e.json())

"""
{
  "is_required": {
    "error_msg": "field required",
    "error_type": "Missing"
  },
  "list_of_ints": {
    "error_msg": "'int' object is not iterable",
    "error_type": "TypeError"
  },
  "recursive_model": {
    "error_msg": "cannot convert dictionary update sequence element #0 to a sequence",
    "error_type": "TypeError",
    "track": "Location"
  }
}
"""
