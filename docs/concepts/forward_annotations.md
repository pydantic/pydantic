## Python 3.14 and greater

Since Python 3.14, Python does not *eagerly* evaluate annotations anymore, meaning you can reference objects
that are not yet defined when the annotation is specified:

```python {requires="3.14" lint="skip"}
from typing import Any

from pydantic import BaseModel


def outer():
    def inner():
        class Model(BaseModel):
            ann: List[Dict[Any, int]]

        Dict = dict

        return Model

    List = list

    Model = inner()

    return Model


Model = outer()

Model(ann=[{'key': '1'}])
#> Model(ann=[{'key': 1}])
```

## Python 3.13 and lower

For Python versions prior to 3.14, References to objects that are not yet defined need to be defined as forward
annotations (wrapped in quotes), or by using the `from __future__ import annotations` [future statement]
(as introduced in [PEP563](https://www.python.org/dev/peps/pep-0563/)):

```python
from __future__ import annotations

from pydantic import BaseModel


class Model(BaseModel):
    a: MyInt
    # Without the future import, equivalent to:
    # a: 'MyInt'


MyInt = int


print(Model(a='1'))
#> a=1
```

The internal logic to resolve forward annotations is described in detail in [this section](../internals/resolving_annotations.md).

## Self-referencing (or "Recursive") Models

Models with self-referencing fields are also supported. These annotations will be resolved during model creation.

=== "Python 3.10 and above"

    ```python
    from pydantic import BaseModel


    class Foo(BaseModel):
        a: int = 123
        sibling: 'Foo | None' = None  # (1)!


    print(Foo())
    #> a=123 sibling=None
    print(Foo(sibling={'a': '321'}))
    #> a=123 sibling=Foo(a=321, sibling=None)
    ```

    1. Python processes annotations when the `Foo` model is being defined (so it isn't actually fully defined yet). As such,
       the `Foo` annotation cannot be resolved, and need to be defined as a forward annotation.

=== "Python 3.14 and above"

    ```python {requires="3.14" lint="skip"}
    from pydantic import BaseModel


    class Foo(BaseModel):
        a: int = 123
        sibling: Foo | None = None


    print(Foo())
    #> a=123 sibling=None
    print(Foo(sibling={'a': '321'}))
    #> a=123 sibling=Foo(a=321, sibling=None)
    ```

## Cyclic imports

When models referencing each other are defined in separate modules, importing one model from the other
module results in a cyclic import: each module needs the other one to be fully imported first.

=== "Python 3.15 and above"

    Python 3.15 introduced [lazy imports](https://docs.python.org/3.15/reference/simple_stmts.html#lazy)
    where the `lazy` keyword defers the actual import until the imported name is first accessed. Lazy
    imports are supported in Pydantic, and can be used to break the cycle:

    ```python {title="a.py" requires="3.15" test="skip" lint="skip"}
    lazy from .b import B

    from pydantic import BaseModel


    class A(BaseModel):
        b: B | None = None
    ```

    ```python {title="b.py" requires="3.15" test="skip" lint="skip"}
    lazy from .a import A

    from pydantic import BaseModel


    class B(BaseModel):
        a: A | None = None
    ```

=== "Python 3.14 and lower"

    For earlier versions, the recommended approach is to only import one of the models in an
    [`if TYPE_CHECKING:`][typing.TYPE_CHECKING] block, and use a forward annotation to reference it:

    ```python {title="a.py" test="skip"}
    from typing import TYPE_CHECKING

    from pydantic import BaseModel

    if TYPE_CHECKING:
        from .b import B


    class A(BaseModel):
        b: 'B | None' = None
    ```

    ```python {title="b.py" test="skip"}
    from pydantic import BaseModel

    from .a import A


    class B(BaseModel):
        a: A | None = None
    ```

    Because `B` isn't available at runtime in `a.py`, the `A` model is left incomplete. In a parent module
    (for instance the package's `__init__.py`), import both models and call
    [`model_rebuild()`][pydantic.BaseModel.model_rebuild] on the incomplete one. As `B` is in scope
    of the calling module, the forward annotation can be resolved:

    ```python {title="__init__.py" test="skip"}
    from .a import A
    from .b import B

    __all__ = ('A', 'B')

    A.model_rebuild()
    ```

[future statement]: https://docs.python.org/3/reference/simple_stmts.html#future
