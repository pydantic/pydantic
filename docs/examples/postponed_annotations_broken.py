from __future__ import annotations
from pydantic import BaseModel


def this_is_broken():
    # Annotations are defined inside the function so is not in the module's
    # global scope!
    from typing import Any, List

    class Model(BaseModel):
        a: List[int]
        b: Any

    print(Model(a=(1, 2), b=3))
