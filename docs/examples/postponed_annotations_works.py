from __future__ import annotations
from typing import Any
from pydantic import BaseModel


def this_works():
    class Model(BaseModel):
        a: list[Any]

    print(Model(a=(1, 2)))
