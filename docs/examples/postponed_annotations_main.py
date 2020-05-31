from __future__ import annotations
from typing import List
from pydantic import BaseModel


class Model(BaseModel):
    a: List[int]


print(Model(a=('1', 2, 3)))
