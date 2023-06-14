Postponed annotations (as described in [PEP563](https://www.python.org/dev/peps/pep-0563/))
"just work".

```py requires="3.9"
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Model(BaseModel):
    a: list[int]
    b: Any


print(Model(a=('1', 2, 3), b='ok'))
#> a=[1, 2, 3] b='ok'
```

Internally, Pydantic will call a method similar to `typing.get_type_hints` to resolve annotations.

Even without using `from __future__ import annotations`, in cases where the referenced type is not yet defined, a
`ForwardRef` or string can be used:

```py
from typing import ForwardRef

from pydantic import BaseModel

Foo = ForwardRef('Foo')


class Foo(BaseModel):
    a: int = 123
    b: Foo = None


print(Foo())
#> a=123 b=None
print(Foo(b={'a': '321'}))
#> a=123 b=Foo(a=321, b=None)
```

## Self-referencing (or "Recursive") Models

Models with self-referencing fields are also supported. Self-referencing fields will be automatically
resolved after model creation.

Within the model, you can refer to the not-yet-constructed model using a string:

```py
from pydantic import BaseModel


class Foo(BaseModel):
    a: int = 123
    #: The sibling of `Foo` is referenced by string
    sibling: 'Foo' = None


print(Foo())
#> a=123 sibling=None
print(Foo(sibling={'a': '321'}))
#> a=123 sibling=Foo(a=321, sibling=None)
```

If you use `from __future__ import annotations`, you can also just refer to the model by its type name:

```py
from __future__ import annotations

from pydantic import BaseModel


class Foo(BaseModel):
    a: int = 123
    #: The sibling of `Foo` is referenced directly by type
    sibling: Foo = None


print(Foo())
#> a=123 sibling=None
print(Foo(sibling={'a': '321'}))
#> a=123 sibling=Foo(a=321, sibling=None)
```
