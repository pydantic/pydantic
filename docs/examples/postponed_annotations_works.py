from __future__ import annotations
from typing import List  # <-- List is defined in the module's global scope
from pydantic import BaseModel


def this_works():
    class Model(BaseModel):
        a: List[int]

    print(Model(a=(1, 2)))
