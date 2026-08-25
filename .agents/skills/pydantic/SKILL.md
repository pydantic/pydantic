---
name: pydantic
description: Pydantic is a Python data validation and serialization library, based on type hints. Use this skill whenever you need to do relatively complex data modeling using Pydantic, e.g. when adding constraints, defining a model hierarchy with subclasses, etc.
---

# Pydantic Validation

In a nutshell, Pydantic is dataclasses with runtime validation. It leverages type hints
to understand how validation (and serialization) should be performed. It is mostly useful
when dealing with external untrusted data, for example when defining an HTTP API.

It is generally *not* recommended to use Pydantic to define classes that are instantiated within the user code.
By doing so, you will lose flexibility (e.g. you cannot use types not supported by Pydantic, and it is harder to perform
post-init changes). It is usually better to use vanilla classes (or standard library dataclasses) in this case,
as a static type checker will already catch type mismatches.

## Basic usage

Here is a simple example of using a Pydantic model:

```python
from datetime import date

from pydantic import BaseModel, Field


class Person(BaseModel):
    name: str
    age: int = Field(description='The age of the person')
    birthdate: date | None = None


p: Person = Person(name='John', age=20, birthdate='1970-01-01')
```

Pydantic coerces compatible input: the ISO date string `'1970-01-01'` is parsed into a `date`.

## Constraints and field metadata

The `Field()` function is used to provide metadata and constraints.
You need to distinguish two types of metadata:

* *field specific* metadata: metadata such as `deprecated` and `alias`, that only
  have meaning when attached to a field.
* *type specific* metadata: this includes constraints such as `gt`, `max_length`,
  and also metadata that affects the JSON Schema (e.g. `description`, `title`).

Model fields are declared with `Field()` using the assignment form:

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    first_name: str = Field(alias='name')
```

or using the annotated pattern:

```python
from typing import Annotated

from pydantic import BaseModel, Field


class Model(BaseModel):
    value: Annotated[int, Field(deprecated=True)] = 1
```

The annotated pattern has some advantages:

* Using the `f: <type> = Field()` form (no default) can be confusing and might trick users into thinking `f`
  has a default value, while in reality the field is still required.
* You can provide an arbitrary amount of metadata elements for a field. As shown in the example above,
  the `Field()` function only supports a limited set of constraints/metadata,
  and you may have to use different Pydantic utilities such as `WithJsonSchema`
  in some cases.

But note that:

* You should use the assignment form for metadata that has a meaning for static type checkers. This includes: `alias`, `default` and `default_factory`.
* *field specific* metadata can only be used on the "top-level" type. A common pitfall
  is to do the following:

    ```python
    from typing import Annotated

    from pydantic import BaseModel, Field


    class Model(BaseModel):
        field_bad: Annotated[int, Field(deprecated=True)] | None = None
        field_ok: Annotated[int | None, Field(deprecated=True)] = None
    ```

  *field specific* metadata should apply to the whole union in this example.

### Constraints

As much as possible, use the "built-in" validation constraints, instead of defining
custom validators:

```python
from typing import Annotated

from annotated_types import Gt  # annotated_types is an alternative to the `Field()` function.
from pydantic import BaseModel, field_validator


class Model(BaseModel):
    constrained_int_ok: Annotated[int, Gt(1)]  # This is good

    constrained_int_bad: int

    @field_validator('constrained_int_bad')  # This is bad
    @classmethod
    def validate(cls, v: int) -> int:
        if not v > 1:
            raise ValueError('Value is not greater than 1')
        return v
```

Sometimes, constraints can't be expressed using the `Field()` function. For example, string constraints such
as `strip_whitespace`, `to_upper`, `to_lower` and `ascii_only` can only be specified using `pydantic.StringConstraints`:

```python
from typing import Annotated

from pydantic import BaseModel, StringConstraints


class Model(BaseModel):
    # Do this instead of a validator calling s.strip():
    a: Annotated[str, StringConstraints(strip_whitespace=True)]
```

<https://pydantic.dev/docs/validation/latest/api/pydantic/standard_library_types/> is the canonical documentation for all
supported standard library types and their constraints.

### Validators

In some cases, you may have to use custom validators. As much as possible, use *after* validators. Because they run after
Pydantic validation, the value is already the field's type. If you use *before* validators,
the input data can literally be anything, so it is more error-prone (especially for model validators, the input isn't
necessarily a dict, it can also be an arbitrary object).

If possible, prefer using the annotated pattern for validators:

```python
from typing import Annotated

from pydantic import AfterValidator, BaseModel, field_validator


def is_even(value: int) -> int:
    if value % 2 == 1:
        raise ValueError(f'{value} is not an even number')
    return value


class Model(BaseModel):
    # Prefer this form: the validator is right next to the field, making it easy to understand
    even: Annotated[int, AfterValidator(is_even)]
    odd: int

    # If you define a validator as decorator, make sure to define it as classmethod.
    @field_validator('odd', mode='after')
    @classmethod
    def is_odd(cls, value: int) -> int:
        if value % 2 == 0:
            raise ValueError(f'{value} is not an odd number')
        return value
```

Using the decorator pattern can lead to unclear behavior, especially regarding the order in which validators run
(in particular on subclasses).

### Type coercion, collections and unions

Unless you are using [strict mode](https://pydantic.dev/docs/validation/latest/concepts/strict_mode/), Pydantic applies
type coercion in most cases. For instance, for a field typed as `int`, strings like `'123'` will be accepted. This also
applies to collection types: `list[str]` also accepts tuples, sets etc.

This is why you should avoid:

* using unions such as `int | str`, if your goal is to coerce the `str` to an `int` via a validator.
* using abstract collections such as `collections.abc.Sequence`, if your goal is to accept both lists and tuples.
  Using these abstract collections is inefficient.

In the general case, unions are best avoided because every use of the field will need to check for each type before
doing anything with it.

### Forward annotations

Python has the ability to write annotations as forward references, by using strings. This can cause challenges for Pydantic
to evaluate them, so they are best avoided if possible.

If you are defining Pydantic models in a module, avoid using `from __future__ import annotations` if possible
(which stringifies all annotations by default). Only add explicit quotes to annotations that aren't defined yet, e.g.:

```python
from pydantic import BaseModel


class Model(BaseModel):
    self_ref: 'Model'
```

Also note that in Python >= 3.14, annotation evaluation is deferred, so you should not use string annotations at all.

#### Recursive type aliases

You might be tempted to define aliases like this:

```python
from typing import TypeAlias

JsonValue: TypeAlias = 'list[JsonValue] | dict[str, JsonValue] | str | bool | int | float | None'
```

The alias needs to be quoted because it is recursive. Pydantic will generally *not* be able to evaluate a quoted `TypeAlias`.
Instead, use an explicit type alias (`type` on Python 3.12+, or `TypeAliasType`), which Pydantic can resolve:

```python
type JsonValue = list[JsonValue] | dict[str, JsonValue] | str | bool | int | float | None
# Or, if not on Python >= 3.12:
from typing_extensions import TypeAliasType

JsonValue = TypeAliasType('JsonValue', 'list[JsonValue] | dict[str, JsonValue] | str | bool | int | float | None')
```

### Model subclasses, discriminated unions

Subclassing is a really common Python pattern, but can be a footgun in Pydantic. You might be tempted to do:

```python
from pydantic import BaseModel


class Base(BaseModel):
    base_field: int

    def common_method(self) -> None: ...


class Sub1(Base):
    sub1_field: str


class Sub2(Base):
    sub2_field: bool


class Main(BaseModel):
    model: Base


m: Main = Main(model=Sub1(base_field=1, sub1_field='test'))
```

This example works, but will not behave as expected when serializing `m`:

```python
m.model_dump()
#> {'model': {'base_field': 1}} -> sub1_field missing
```

This is because Pydantic serializes according to the declared type (`Base`), not the runtime subclass.
Validation follows the same rule: `Main(model={'base_field': 1, 'sub1_field': 'test'})` validates against `Base`,
so `sub1_field` is ignored rather than producing a `Sub1` instance.

Instead, try to use discriminated unions (provided that you can set a `type` field to distinguish models):

```python
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, Field


class Sub1(Base):
    type: Literal['sub1']
    sub1_field: str


class Sub2(Base):
    type: Literal['sub2']
    sub2_field: bool


Subs: TypeAlias = Annotated[Sub1 | Sub2, Field(discriminator='type')]


class Main(BaseModel):
    model: Subs
```

or generics:

```python
from pydantic import BaseModel


class Main[BaseT: Base](BaseModel):
    model: BaseT


m: Main[Sub1] = Main[Sub1](model={'base_field': 1, 'sub1_field': 'test'})  # Will work
```

If neither discriminated unions nor generics fit, [polymorphic serialization](https://pydantic.dev/docs/validation/latest/concepts/serialization/#polymorphic-serialization) (in Pydantic >=2.13)
or [*serialize as any*](https://pydantic.dev/docs/validation/latest/concepts/serialization/#serializing-as-any) (in Pydantic <2.13)
can be used as a last resort.
