from typing import NamedTuple

from pydantic import BaseModel, ValidationError


class Point(NamedTuple):
    x: int
    y: int


class Model(BaseModel):
    p: Point


print(Model(p=('1', '2')))

try:
    Model(p=('1.3', '2'))
except ValidationError as e:
    print(e)
