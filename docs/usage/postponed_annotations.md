!!! note
    Both postponed annotations via the future import and `ForwardRef` require Python 3.7+.

Postponed annotations (as described in [PEP563](https://www.python.org/dev/peps/pep-0563/))
"just work".

```py
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Model(BaseModel):
    a: list[int]
    b: Any


print(Model(a=('1', 2, 3), b='ok'))
#> a=[1, 2, 3] b='ok'
```

Internally, *pydantic*  will call a method similar to `typing.get_type_hints` to resolve annotations.

In cases where the referenced type is not yet defined, `ForwardRef` can be used (although referencing the
type directly or by its string is a simpler solution in the case of
[self-referencing models](#self-referencing-models)).

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

When the referenced type is not defined yet, and reference it by string, you'll need to call `model_rebuild`
after the model has been created before it can be used:

```py
from pydantic import BaseModel


class Bar(BaseModel):
    foo: 'Foo'


class Foo(BaseModel):
    x: int


Bar.model_rebuild()

print(Bar(foo={'x': '123'}))
#> foo=Foo(x=123)
```

## Self-referencing Models

Data structures with self-referencing models are also supported. Self-referencing fields will be automatically
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

Since Python 3.7, you can also refer it by its type, provided you import `annotations` (see
[above](postponed_annotations.md) for support depending on Python
and *pydantic* versions).

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
