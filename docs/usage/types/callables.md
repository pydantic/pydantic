---
description: Support for callable types.
---

`typing.Callable`
: see below for more detail on parsing and validation

Fields can also be of type `Callable`:

```py
from typing import Callable

from pydantic import BaseModel


class Foo(BaseModel):
    callback: Callable[[int], int]


m = Foo(callback=lambda x: x)
print(m)
#> callback=<function <lambda> at 0x0123456789ab>
```

!!! warning
    Callable fields only perform a simple check that the argument is
    callable; no validation of arguments, their types, or the return
    type is performed.
