from typing import List

from pydantic import BaseModel, Json, ValidationError


class SimpleJsonModel(BaseModel):
    json_obj: Json


class ComplexJsonModel(BaseModel):
    json_obj: Json[List[int]]


print(SimpleJsonModel(json_obj='{"b": 1}'))
print(ComplexJsonModel(json_obj='[1, 2, 3]'))
try:
    ComplexJsonModel(json_obj=12)
except ValidationError as e:
    print(e)

try:
    ComplexJsonModel(json_obj='[a, b]')
except ValidationError as e:
    print(e)

try:
    ComplexJsonModel(json_obj='["a", "b"]')
except ValidationError as e:
    print(e)
