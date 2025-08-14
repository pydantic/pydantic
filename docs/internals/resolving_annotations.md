!!! note
    This section is part of the *internals* documentation, and is partly targeted to contributors.

Pydantic heavily relies on [type hints][type hint] at runtime to build schemas for validation, serialization, etc.

While type hints were primarily introduced for static type checkers (such as [Mypy] or [Pyright]), they are
accessible (and sometimes evaluated) at runtime. This means that the following would fail at runtime,
because `Node` has yet to be defined in the current module:

```python {test="skip" lint="skip"}
class Node:
    """Binary tree node."""

    # NameError: name 'Node' is not defined:
    def __init__(self, l: Node, r: Node) -> None:
        self.left = l
        self.right = r
```

To circumvent this issue, forward references can be used (by wrapping the annotation in quotes).

In Python 3.7, [PEP 563] introduced the concept of _postponed evaluation of annotations_, meaning
with the `from __future__ import annotations` [future statement], type hints are stringified by default:

```python {requires="3.12" lint="skip"}
from __future__ import annotations

from pydantic import BaseModel


class Foo(BaseModel):
    f: MyType
    # Given the future import above, this is equivalent to:
    # f: 'MyType'


type MyType = int

print(Foo.__annotations__)
#> {'f': 'MyType'}
```

## The challenges of runtime evaluation

Static type checkers make use of the <abbr title="Abstract Syntax Tree">AST</abbr> to analyze the defined annotations.
Regarding the previous example, this has the benefit of being able to understand what `MyType` refers to when analyzing
the class definition of `Foo`, even if `MyType` isn't yet defined at runtime.

However, for runtime tools such as Pydantic, it is more challenging to correctly resolve these forward annotations.
The Python standard library provides some tools to do so ([`typing.get_type_hints()`][typing.get_type_hints],
[`inspect.get_annotations()`][inspect.get_annotations]), but they come with some limitations. Thus, they are
being re-implemented in Pydantic with improved support for edge cases.

As Pydantic as grown, it's adapted to support many edge cases requiring irregular patterns for annotation evaluation.
Some of these use cases aren't necessarily sound from a static type checking perspective. In v2.10, the internal
logic was refactored in an attempt to simplify and standardize annotation evaluation. Admittedly, backwards compatibility
posed some challenges, and there is still some noticeable scar tissue in the codebase because of this.There's a hope that
[PEP 649] (introduced in Python 3.14) will greatly simplify the process, especially when it comes to dealing with locals
of a function.

To evaluate forward references, Pydantic roughly follows the same logic as described in the documentation of the
[`typing.get_type_hints()`][typing.get_type_hints] function. That is, the built-in [`eval()`][eval] function is used
by passing the forward reference, a global, and a local namespace. The namespace fetching logic is defined in the
sections below.

## Resolving annotations at class definition

The following example will be used as a reference throughout this section:

```python {test="skip" lint="skip"}
# module1.py:
type MyType = int

class Base:
    f1: 'MyType'

# module2.py:
from pydantic import BaseModel

from module1 import Base

type MyType = str


def inner() -> None:
    type InnerType = bool

    class Model(BaseModel, Base):
        type LocalType = bytes

        f2: 'MyType'
        f3: 'InnerType'
        f4: 'LocalType'
        f5: 'UnknownType'

    type InnerType2 = complex
```

When the `Model` class is being built, different [namespaces][namespace] are at play. For each base class
of the `Model`'s [MRO][method resolution order] (in reverse order — that is, starting with `Base`), the
following logic is applied:

1. Fetch the `__annotations__` key from the current base class' `__dict__`, if present. For `Base`, this will be
   `{'f1': 'MyType'}`.
2. Iterate over the `__annotations__` items and try to evaluate the annotation [^1] using a custom wrapper around
   the built-in [`eval()`][eval] function. This function takes two `globals` and `locals` arguments:
     - The current module's `__dict__` is naturally used as `globals`. For `Base`, this will be
       `sys.modules['module1'].__dict__`.
     - For the `locals` argument, Pydantic will try to resolve symbols in the following namespaces, sorted by highest priority:
         - A namespace created on the fly, containing the current class name (`{cls.__name__: cls}`). This is done
           in order to support recursive references.
         - The locals of the current class (i.e. `cls.__dict__`). For `Model`, this will include `LocalType`.
         - The parent namespace of the class, if different from the globals described above. This is the
           [locals][frame.f_locals] of the frame where the class is being defined. For `Base`, because the class is being
           defined in the module directly, this namespace won't be used as it will result in the globals being used again.
           For `Model`, the parent namespace is the locals of the frame of `inner()`.
3. If the annotation failed to evaluate, it is kept as is, so that the model can be rebuilt at a later stage. This will
   be the case for `f5`.

The following table lists the resolved type annotations for every field, once the `Model` class has been created:

| Field name | Resolved annotation |
|------------|---------------------|
| `f1`       | [`int`][]           |
| `f2`       | [`str`][]           |
| `f3`       | [`bool`][]          |
| `f4`       | [`bytes`][]         |
| `f5`       | `'UnkownType'`      |

### Limitations and backwards compatibility concerns

While the namespace fetching logic is trying to be as accurate as possible, we still face some limitations:

<div class="annotate" markdown>

- The locals of the current class (`cls.__dict__`) may include irrelevant entries, most of them being dunder attributes.
  This means that the following annotation: `f: '__doc__'` will successfully (and unexpectedly) be resolved.
- When the `Model` class is being created inside a function, we keep a copy of the [locals][frame.f_locals] of the frame.
  This copy only includes the symbols defined in the locals when `Model` is being defined, meaning `InnerType2` won't be included
  (and will **not be** if doing a model rebuild at a later point!).
    - To avoid memory leaks, we use [weak references][weakref] to the locals of the function, meaning some forward references might
    not resolve outside the function (1).
    - Locals of the function are only taken into account for Pydantic models, but this pattern does not apply to dataclasses, typed
    dictionaries or named tuples.

</div>

1.  Here is an example:

    ```python {test="skip" lint="skip"}
    def func():
        A = int

        class Model(BaseModel):
            f: 'A | Forward'

        return Model


    Model = func()

    Model.model_rebuild(_types_namespace={'Forward': str})
    # pydantic.errors.PydanticUndefinedAnnotation: name 'A' is not defined
    ```

[](){#backwards-compatibility-logic}

For backwards compatibility reasons, and to be able to support valid use cases without having to rebuild models,
the namespace logic described above is a bit different when it comes to core schema generation. Taking the
following example:

```python
from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class Foo:
    a: 'Bar | None' = None


class Bar(BaseModel):
    b: Foo
```

Once the fields for `Bar` have been collected (meaning annotations resolved), the `GenerateSchema` class converts
every field into a core schema. When it encounters another class-like field type (such as a dataclass), it will
try to evaluate annotations, following roughly the same logic as [described above](#resolving-annotations-at-class-definition).
However, to evaluate the `'Bar | None'` annotation, `Bar` needs to be present in the globals or locals, which is normally
*not* the case: `Bar` is being created, so it is not "assigned" to the current module's `__dict__` at that point.

To avoid having to call [`model_rebuild()`][pydantic.BaseModel.model_rebuild] on `Bar`, both the parent namespace
(if `Bar` was to be defined inside a function, and [the namespace provided during a model rebuild](#model-rebuild-semantics))
and the `{Bar.__name__: Bar}` namespace are included in the locals during annotations evaluation of `Foo`
(with the lowest priority) (1).
{ .annotate }

1.  This backwards compatibility logic can introduce some inconsistencies, such as the following:

    ```python {lint="skip"}
    from dataclasses import dataclass

    from pydantic import BaseModel


    @dataclass
    class Foo:
        # `a` and `b` shouldn't resolve:
        a: 'Model'
        b: 'Inner'


    def func():
        Inner = int

        class Model(BaseModel):
            foo: Foo

        Model.__pydantic_complete__
        #> True, should be False.
    ```

## Resolving annotations when rebuilding a model

When a forward reference fails to evaluate, Pydantic will silently fail and stop the core schema
generation process. This can be seen by inspecting the `__pydantic_core_schema__` of a model class:

```python {lint="skip"}
from pydantic import BaseModel


class Foo(BaseModel):
    f: 'MyType'


Foo.__pydantic_core_schema__
#> <pydantic._internal._mock_val_ser.MockCoreSchema object at 0x73cd0d9e6d00>
```

If you then properly define `MyType`, you can rebuild the model:

```python {test="skip" lint="skip"}
type MyType = int

Foo.model_rebuild()
Foo.__pydantic_core_schema__
#> {'type': 'model', 'schema': {...}, ...}
```

[](){#model-rebuild-semantics}

The [`model_rebuild()`][pydantic.BaseModel.model_rebuild] method uses a *rebuild namespace*, with the following semantics:

- If an explicit `_types_namespace` argument is provided, it is used as the rebuild namespace.
- If no namespace is provided, the namespace where the method is called will be used as the rebuild namespace.

This *rebuild namespace* will be merged with the model's parent namespace (if it was defined in a function) and used as is
(see the [backwards compatibility logic](#backwards-compatibility-logic) described above).

[Mypy]: https://www.mypy-lang.org/
[Pyright]: https://github.com/microsoft/pyright/
[PEP 563]: https://peps.python.org/pep-0563/
[PEP 649]: https://peps.python.org/pep-0649/
[future statement]: https://docs.python.org/3/reference/simple_stmts.html#future

[^1]: This is done unconditionally, as forward annotations can be only present _as part_ of a type hint (e.g. `Optional['int']`), as dictated by
      the [typing specification](https://typing.readthedocs.io/en/latest/spec/annotations.html#string-annotations).
