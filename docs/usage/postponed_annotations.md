!!! note
    Both postponed annotations via the future import and `ForwardRef` require Python 3.7+.

Postponed annotations (as described in [PEP563](https://www.python.org/dev/peps/pep-0563/))
"just work".

```py requires="3.8" upgrade="skip"
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

In some cases, a `ForwardRef` won't be able to be resolved during model creation.
For example, this happens whenever a model references itself as a field type.
When this happens, you'll need to call `update_forward_refs` after the model has been created before it can be used:

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

!!! warning
    To resolve strings (type names) into annotations (types), *pydantic* needs a namespace dict in which to
    perform the lookup. For this it uses `module.__dict__`, just like `get_type_hints`.
    This means *pydantic* may not play well with types not defined in the global scope of a module.

For example, this works fine:

```py test="xfail - this should work"
from __future__ import annotations

from pydantic import (
    BaseModel,
    HttpUrl,  # HttpUrl is defined in the module's global scope
)


def this_works():
    class Model(BaseModel):
        a: HttpUrl

    print(Model(a='https://example.com'))


this_works()
```

While this will break:

```py
from __future__ import annotations

from pydantic import BaseModel
from pydantic.errors import PydanticUserError


def this_is_broken():
    from pydantic import HttpUrl  # HttpUrl is defined in function local scope

    class Model(BaseModel):
        a: HttpUrl

    try:
        Model(a='https://example.com')
    except PydanticUserError as e:
        print(e)

    try:
        Model.model_rebuild()
    except NameError as e:
        print(e)


this_is_broken()
```

Resolving this is beyond the call for *pydantic*: either remove the future import or declare the types globally.

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
