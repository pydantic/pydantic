??? api "API Documentation"
    [`pydantic.types.Strict`][pydantic.types.Strict]<br>

By default, Pydantic will attempt to coerce values to the desired type when possible.
For example, you can pass the string `"123"` as the input to an `int` field, and it will be converted to `123`.
This coercion behavior is useful in many scenarios — think: UUIDs, URL parameters, HTTP headers, environment variables,
user input, etc.

However, there are also situations where this is not desirable, and you want Pydantic to error instead of coercing data.

To better support this use case, Pydantic provides a "strict mode" that can be enabled on a per-model, per-field, or
even per-validation-call basis. When strict mode is enabled, Pydantic will be much less lenient when coercing data,
and will instead error if the data is not of the correct type.

Here is a brief example showing the difference between validation behavior in strict and the default/"lax" mode:

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

There are various ways to get strict-mode validation while using Pydantic, which will be discussed in more detail below:

* [Passing `strict=True` to the validation methods](#strict-mode-in-method-calls), such as `BaseModel.model_validate`,
  `TypeAdapter.validate_python`, and similar for JSON
* [Using `Field(strict=True)`](#strict-mode-with-field) with fields of a `BaseModel`, `dataclass`, or `TypedDict`
* [Using `pydantic.types.Strict` as a type annotation](#strict-mode-with-annotated-strict) on a field
  * Pydantic provides some type aliases that are already annotated with `Strict`, such as `pydantic.types.StrictInt`
* [Using `ConfigDict(strict=True)`](#strict-mode-with-configdict)

## Type coercions in strict mode

For most types, when validating data from python in strict mode, only the instances of the exact types are accepted.
For example, when validating an `int` field, only instances of `int` are accepted; passing instances of `float` or `str`
will result in raising a `ValidationError`.

Note that we are looser when validating data from JSON in strict mode. For example, when validating a `UUID` field,
instances of `str` will be accepted when validating from JSON, but not from python:

```python
import json
from uuid import UUID

from pydantic import BaseModel, ValidationError


class MyModel(BaseModel):
    guid: UUID


data = {'guid': '12345678-1234-1234-1234-123456789012'}

print(MyModel.model_validate(data))  # OK: lax
#> guid=UUID('12345678-1234-1234-1234-123456789012')

print(
    MyModel.model_validate_json(json.dumps(data), strict=True)
)  # OK: strict, but from json
#> guid=UUID('12345678-1234-1234-1234-123456789012')

try:
    MyModel.model_validate(data, strict=True)  # Not OK: strict, from python
except ValidationError as exc:
    print(exc.errors(include_url=False))
    """
    [
        {
            'type': 'is_instance_of',
            'loc': ('guid',),
            'msg': 'Input should be an instance of UUID',
            'input': '12345678-1234-1234-1234-123456789012',
            'ctx': {'class': 'UUID'},
        }
    ]
    """
```

For more details about what types are allowed as inputs in strict mode, you can review the
[Conversion Table](conversion_table.md).

## Strict mode in method calls

All the examples included so far get strict-mode validation through the use of `strict=True` as a keyword argument to
the validation methods. While we have shown this for `BaseModel.model_validate`, this also works with arbitrary types
through the use of `TypeAdapter`:

```python
from pydantic import TypeAdapter, ValidationError

print(TypeAdapter(bool).validate_python('yes'))  # OK: lax
#> True

try:
    TypeAdapter(bool).validate_python('yes', strict=True)  # Not OK: strict
except ValidationError as exc:
    print(exc)
    """
    1 validation error for bool
      Input should be a valid boolean [type=bool_type, input_value='yes', input_type=str]
    """
```

Note this also works even when using more "complex" types in `TypeAdapter`:
```python
from dataclasses import dataclass

from pydantic import TypeAdapter, ValidationError


@dataclass
class MyDataclass:
    x: int


try:
    TypeAdapter(MyDataclass).validate_python({'x': '123'}, strict=True)
except ValidationError as exc:
    print(exc)
    """
    1 validation error for MyDataclass
      Input should be an instance of MyDataclass [type=dataclass_exact_type, input_value={'x': '123'}, input_type=dict]
    """
```

This also works with the `TypeAdapter.validate_json` and `BaseModel.model_validate_json` methods:

```python
import json
from typing import List
from uuid import UUID

from pydantic import BaseModel, TypeAdapter, ValidationError

try:
    TypeAdapter(List[int]).validate_json('["1", 2, "3"]', strict=True)
except ValidationError as exc:
    print(exc)
    """
    2 validation errors for list[int]
    0
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    2
      Input should be a valid integer [type=int_type, input_value='3', input_type=str]
    """


class Model(BaseModel):
    x: int
    y: UUID


data = {'x': '1', 'y': '12345678-1234-1234-1234-123456789012'}
try:
    Model.model_validate(data, strict=True)
except ValidationError as exc:
    # Neither x nor y are valid in strict mode from python:
    print(exc)
    """
    2 validation errors for Model
    x
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    y
      Input should be an instance of UUID [type=is_instance_of, input_value='12345678-1234-1234-1234-123456789012', input_type=str]
    """

json_data = json.dumps(data)
try:
    Model.model_validate_json(json_data, strict=True)
except ValidationError as exc:
    # From JSON, x is still not valid in strict mode, but y is:
    print(exc)
    """
    1 validation error for Model
    x
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```


## Strict mode with `Field`

For individual fields on a model, you can [set `strict=True` on the field](../api/fields.md#pydantic.fields.Field).
This will cause strict-mode validation to be used for that field, even when the validation methods are called without
`strict=True`.

Only the fields for which `strict=True` is set will be affected:

```python
from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    name: str
    age: int
    n_pets: int


user = User(name='John', age='42', n_pets='1')
print(user)
#> name='John' age=42 n_pets=1


class AnotherUser(BaseModel):
    name: str
    age: int = Field(strict=True)
    n_pets: int


try:
    anotheruser = AnotherUser(name='John', age='42', n_pets='1')
except ValidationError as e:
    print(e)
    """
    1 validation error for AnotherUser
    age
      Input should be a valid integer [type=int_type, input_value='42', input_type=str]
    """
```

Note that making fields strict will also affect the validation performed when instantiating the model class:

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(strict=True)
    y: int = Field(strict=False)


try:
    Model(x='1', y='2')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Model
    x
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```

### Using `Field` as an annotation

Note that `Field(strict=True)` (or with any other keyword arguments) can be used as an annotation if necessary, e.g.,
when working with `TypedDict`:

```python
from typing_extensions import Annotated, TypedDict

from pydantic import Field, TypeAdapter, ValidationError


class MyDict(TypedDict):
    x: Annotated[int, Field(strict=True)]


try:
    TypeAdapter(MyDict).validate_python({'x': '1'})
except ValidationError as exc:
    print(exc)
    """
    1 validation error for typed-dict
    x
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```

## Strict mode with `Annotated[..., Strict()]`

??? api "API Documentation"
    [`pydantic.types.Strict`][pydantic.types.Strict]<br>

Pydantic also provides the [`Strict`](../api/types.md#pydantic.types.Strict) class, which is intended for use as
metadata with [`typing.Annotated`][] class; this annotation indicates that the annotated field should be validated in
strict mode:

```python
from typing_extensions import Annotated

from pydantic import BaseModel, Strict, ValidationError


class User(BaseModel):
    name: str
    age: int
    is_active: Annotated[bool, Strict()]


User(name='David', age=33, is_active=True)
try:
    User(name='David', age=33, is_active='True')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for User
    is_active
      Input should be a valid boolean [type=bool_type, input_value='True', input_type=str]
    """
```

This is, in fact, the method used to implement some of the strict-out-of-the-box types provided by Pydantic,
such as [`StrictInt`](../api/types.md#pydantic.types.StrictInt).

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

However, if this is _not_ possible (e.g., when working with third-party types), you can set the config that Pydantic
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
    1 validation error for typed-dict
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
