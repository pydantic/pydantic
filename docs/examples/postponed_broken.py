from __future__ import annotations
from pydantic import BaseModel

def this_is_broken():
    from typing import List  # <-- List is defined inside the function so is not in the module's global scope
    class Model(BaseModel):
        a: List[int]
    print(Model(a=(1, 2)))
