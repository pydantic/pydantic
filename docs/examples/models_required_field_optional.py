from typing import Optional
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    a: Optional[int]
    b: Optional[int] = ...
    c: Optional[int] = Field(...)


print(Model(b=1, c=2))
try:
    Model(a=1, b=2)
except ValidationError as e:
    print(e)
