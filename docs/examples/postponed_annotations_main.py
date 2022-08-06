from __future__ import annotations
from typing import Any
from pydantic import BaseModel


class Model(BaseModel):
    a: list[int]
    b: Any


print(Model(a=('1', 2, 3), b='ok'))
