from typing import Callable
from pydantic import BaseModel

class Foo(BaseModel):
    callback: Callable[[int], int]

m = Foo(callback=lambda x: x)
print(m)
# Foo callback=<function <lambda> at 0x7f16bc73e1e0>
