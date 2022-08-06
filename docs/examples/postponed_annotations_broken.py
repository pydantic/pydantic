from __future__ import annotations
from pydantic import BaseModel


def this_is_broken():
    # Any is defined inside the function so is not in the module's
    # global scope!
    from typing import Any

    class Model(BaseModel):
        a: list[int]
        b: Any

    print(Model(a=(1, 2), b=3))
