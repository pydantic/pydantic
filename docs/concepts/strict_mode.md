??? api "API Documentation"
    [`pydantic.types.Strict`][pydantic.types.Strict]<br>

By default, Pydantic will attempt to coerce values to the desired type when possible.
For example, you can pass the string `'123'` as the input for the [`int` number type](../api/standard_library_types.md#integers),
and it will be converted to the value`123`.
This coercion behavior is useful in many scenarios — think: UUIDs, URL parameters, HTTP headers, environment variables,
dates, etc.

However, there are also situations where this is not desirable, and you want Pydantic to error instead of coercing data.

To better support this use case, Pydantic provides a "strict mode". When strict mode is enabled, Pydantic will be much
less lenient when coercing data, and will instead error if the data is not of the correct type.

Most of the time, strict mode will only allow instances of the type to be provided, although looser rules may apply
to JSON input (for instance, the [date and time types](../api/standard_library_types.md#date-and-time-types) allow strings
even in strict mode).

The strict behavior for each type can be found in the [standard library types](../api/standard_library_types.md) documentation,
and is summarized in the [conversion table](./conversion_table.md).

Here is a brief example showing the validation behavior difference in strict and the default lax mode:

```python
from pydantic import BaseModel, ValidationError


class MyModel(BaseModel):
    x: int


print(MyModel.model_validate({'x': '123'}))  # lax mode
#> x=123

try:
    MyModel.model_validate({'x': '123'}, strict=True)  # strict mode
except ValidationError as exc:
    print(exc)
    """
    1 validation error for MyModel
    x
      Input should be a valid integer [type=int_type, input_value='123', input_type=str]
    """
```

Strict mode can be enabled in various ways:

* [Passing `strict=True` to the validation methods](#strict-mode-in-method-calls), such as `BaseModel.model_validate`,
  `TypeAdapter.validate_python`, and similar for JSON
* [Using `Field(strict=True)`](#strict-mode-with-field) with fields of a `BaseModel`, `dataclass`, or `TypedDict`
* [Using `pydantic.types.Strict` as a type annotation](#strict-mode-with-annotated-strict) on a field
    * Pydantic provides some type aliases that are already annotated with `Strict`, such as `pydantic.types.StrictInt`
* [Using `ConfigDict(strict=True)`](#strict-mode-with-configdict)


<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#strict-mode-in-method-calls}
## Strict mode as a validation parameter

Strict mode can be enaled on a per-validation-call basis, when using the [validation methods](./models.md#validating-data)
on Pydantic models and [type adapters](./type_adapter.md).

```python
from datetime import date

from pydantic import TypeAdapter, ValidationError


print(TypeAdapter(date).validate_python('2000-01-01'))  # OK: lax
#> 2000-01-01

try:
    TypeAdapter(date).validate_python('2000-01-01', strict=True)  # Not OK: strict
except ValidationError as exc:
    print(exc)
    """
    1 validation error for date
      Input should be a valid date [type=date_type, input_value='2000-01-01', input_type=str]
    """

TypeAdapter(date).validate_json('"2000-01-01"', strict=True)  # (1)!
#> 2000-01-01
```

1. As mentioned, strict mode is looser when validating from JSON.

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#strict-mode-with-field}
## Strict mode at the field level

Strict mode can be enabled on specific fields, by setting the `strict` parameter of the
[`Field()`][pydantic.Field] function to `True`. Strict mode will be applied for such fields,
even when the [validation methods](./models.md#validating-data) are called in lax mode.


```python
from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    name: str
    age: int = Field(strict=True)  # (1)!


user = User(name='John', age=42)
print(user)
#> name='John' age=42


try:
    another_user = User(name='John', age='42')
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    age
      Input should be a valid integer [type=int_type, input_value='42', input_type=str]
    """
```

1. The strict constraint can also be applied using the [annotated pattern](./fields.md#the-annotated-pattern):
   `Annotated[int, Field(strict=True)]`

<!-- old anchor added for backwards compatibility -->
<!-- markdownlint-disable-next-line no-empty-links -->
[](){#strict-mode-with-annotated-strict}
### Using the `Strict()` metadata class

??? api "API Documentation"
    [`pydantic.types.Strict`][pydantic.types.Strict]<br>

As an alternative to the [`Field()`][pydantic.Field] function, Pydantic provides the [`Strict`][pydantic.types.Strict]
metadata class, meant to be used with the [annotated pattern](./fields.md#the-annotated-pattern). It also provides
convenience aliases for the most common types (namely [`StrictBool`][pydantic.types.StrictBool],
[`StrictInt`][pydantic.types.StrictInt], [`StrictFloat`][pydantic.types.StrictFloat], [`StrictStr`][pydantic.types.StrictStr]
and [`StrictBytes`][pydantic.types.StrictBytes]).

```python
from uuid import UUID

from pydantic import BaseModel, Strict, StrictInt


class User(BaseModel):
    id: Annotated[UUID, Strict()]
    age: StrictInt  # (1)!
```

1. Equivalent to `Annotated[int, Strict()]`.

## Strict mode with `ConfigDict`

### `BaseModel`

If you want to enable strict mode for all fields on a complex input type, you can use
[`ConfigDict(strict=True)`](../api/config.md#pydantic.config.ConfigDict) in the `model_config`:

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class User(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    age: int
    is_active: bool


try:
    User(name='David', age='33', is_active='yes')
except ValidationError as exc:
    print(exc)
    """
    2 validation errors for User
    age
      Input should be a valid integer [type=int_type, input_value='33', input_type=str]
    is_active
      Input should be a valid boolean [type=bool_type, input_value='yes', input_type=str]
    """
```

!!! note
    When using `strict=True` through a model's `model_config`, you can still override the strictness
    of individual fields by setting `strict=False` on individual fields:

    ```python
    from pydantic import BaseModel, ConfigDict, Field


    class User(BaseModel):
        model_config = ConfigDict(strict=True)

        name: str
        age: int = Field(strict=False)
    ```

Note that strict mode is not recursively applied to nested model fields:

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class Inner(BaseModel):
    y: int


class Outer(BaseModel):
    model_config = ConfigDict(strict=True)

    x: int
    inner: Inner


print(Outer(x=1, inner=Inner(y='2')))
#> x=1 inner=Inner(y=2)

try:
    Outer(x='1', inner=Inner(y='2'))
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Outer
    x
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```

(This is also the case for dataclasses and `TypedDict`.)

If this is undesirable, you should make sure that strict mode is enabled for all the types involved.
For example, this can be done for model classes by using a shared base class with
`model_config = ConfigDict(strict=True)`:

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class MyBaseModel(BaseModel):
    model_config = ConfigDict(strict=True)


class Inner(MyBaseModel):
    y: int


class Outer(MyBaseModel):
    x: int
    inner: Inner


try:
    Outer.model_validate({'x': 1, 'inner': {'y': '2'}})
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Outer
    inner.y
      Input should be a valid integer [type=int_type, input_value='2', input_type=str]
    """
```

### Dataclasses and `TypedDict`

Pydantic dataclasses behave similarly to the examples shown above with `BaseModel`, just that instead of `model_config`
you should use the `config` keyword argument to the `@pydantic.dataclasses.dataclass` decorator.

When possible, you can achieve nested strict mode for vanilla dataclasses or `TypedDict` subclasses by annotating fields
with the [`pydantic.types.Strict` annotation](#strict-mode-with-annotated-strict).

However, if this is *not* possible (e.g., when working with third-party types), you can set the config that Pydantic
should use for the type by setting the `__pydantic_config__` attribute on the type:

```python
from typing_extensions import TypedDict

from pydantic import ConfigDict, TypeAdapter, ValidationError


class Inner(TypedDict):
    y: int


Inner.__pydantic_config__ = ConfigDict(strict=True)


class Outer(TypedDict):
    x: int
    inner: Inner


adapter = TypeAdapter(Outer)
print(adapter.validate_python({'x': '1', 'inner': {'y': 2}}))
#> {'x': 1, 'inner': {'y': 2}}


try:
    adapter.validate_python({'x': '1', 'inner': {'y': '2'}})
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Outer
    inner.y
      Input should be a valid integer [type=int_type, input_value='2', input_type=str]
    """
```

### `TypeAdapter`

You can also get strict mode through the use of the config keyword argument to the
[`TypeAdapter`](../api/type_adapter.md) class:

```python
from pydantic import ConfigDict, TypeAdapter, ValidationError

adapter = TypeAdapter(bool, config=ConfigDict(strict=True))

try:
    adapter.validate_python('yes')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for bool
      Input should be a valid boolean [type=bool_type, input_value='yes', input_type=str]
    """
```

### `@validate_call`

Strict mode is also usable with the [`@validate_call`](../api/validate_call.md#pydantic.validate_call_decorator.validate_call)
decorator by passing the `config` keyword argument:

```python
from pydantic import ConfigDict, ValidationError, validate_call


@validate_call(config=ConfigDict(strict=True))
def foo(x: int) -> int:
    return x


try:
    foo('1')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for foo
    0
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```
