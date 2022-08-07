from __future__ import annotations
from typing import Any, List
from pydantic import BaseModel


def this_works():
    class Model(BaseModel):
        a: List[Any]

    print(Model(a=(1, 2)))
