from typing import Any, List

from pydantic import BaseModel, Json, ValidationError


class AnyJsonModel(BaseModel):
    json_obj: Json[Any]


class ConstrainedJsonModel(BaseModel):
    json_obj: Json[List[int]]


print(AnyJsonModel(json_obj='{"b": 1}'))
print(ConstrainedJsonModel(json_obj='[1, 2, 3]'))
try:
    ConstrainedJsonModel(json_obj=12)
except ValidationError as e:
    print(e)

try:
    ConstrainedJsonModel(json_obj='[a, b]')
except ValidationError as e:
    print(e)

try:
    ConstrainedJsonModel(json_obj='["a", "b"]')
except ValidationError as e:
    print(e)
