from typing import List
from pydantic import BaseModel, ValidationError, conint


class Location(BaseModel):
    lat = 0.1
    lng = 10.1


class Model(BaseModel):
    is_required: float
    gt_int: conint(gt=42)
    list_of_ints: List[int] = None
    a_float: float = None
    recursive_model: Location = None


data = dict(
    list_of_ints=['1', 2, 'bad'],
    a_float='not a float',
    recursive_model={'lat': 4.2, 'lng': 'New York'},
    gt_int=21,
)

try:
    Model(**data)
except ValidationError as e:
    print(e)

try:
    Model(**data)
except ValidationError as e:
    print(e.json())
