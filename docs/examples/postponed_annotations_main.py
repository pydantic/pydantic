from __future__ import annotations
from typing import Any, List
from pydantic import BaseModel


class Model(BaseModel):
    a: List[int]
    b: Any


print(Model(a=('1', 2, 3), b='ok'))
