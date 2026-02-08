??? api "API Documentation"
    [`@pydantic.dataclasses.dataclass`][pydantic.dataclasses.dataclass]<br>

If you don't want to use Pydantic's [`BaseModel`][pydantic.BaseModel] you can instead get the same data validation
on standard [dataclasses][dataclasses].

```python
from datetime import datetime
from typing import Optional

from pydantic.dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str = 'John Doe'
    signup_ts: Optional[datetime] = None


user = User(id='42', signup_ts='2032-06-21T12:00')
print(user)
"""
User(id=42, name='John Doe', signup_ts=datetime.datetime(2032, 6, 21, 12, 0))
"""
```

!!! note
    Keep in mind that Pydantic dataclasses are **not** a replacement for [Pydantic models](../concepts/models.md).
    They provide a similar functionality to stdlib dataclasses with the addition of Pydantic validation.

    There are cases where using Pydantic models is the better choice.

    For more information and discussion see
    [pydantic/pydantic#710](https://github.com/pydantic/pydantic/issues/710).

Similarities between Pydantic dataclasses and models include support for:

* [Configuration](#dataclass-config) support (even though dataclasses doesn't support the `model_config` attribute as with Pydantic models)
* [Nested](./models.md#nested-models) classes
* Arguments used to instantiate the dataclass are also [copied](./models.md#attribute-copies).

Some differences between Pydantic dataclasses and models include:

* The [various methods](./models.md#model-methods-and-properties) to validate, dump and generate a JSON Schema aren't available. Instead,
  you can wrap the dataclass with a [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] and make use of its methods:

    ```python
    from pydantic import TypeAdapter
    from pydantic.dataclasses import dataclass


    @dataclass
    class Foo:
        f: int


    foo = Foo(f=1)

    TypeAdapter(Foo).dump_python(foo)
    #> {'f': 1}
    TypeAdapter(Foo).validate_python({'f': 1})
    #> Foo(f=1)
    ```

* Validators (see the [dedicated section](#validators-and-initialization-hooks)).
* The [`extra`][pydantic.ConfigDict.extra] configuration behavior:
    * Extra data is not included in [serialization](./serialization.md#serializing-data).
    * There is no way to customize validation of extra values [using the `__pydantic_extra__` attribute](./models.md#extra-data).
* Generic dataclasses are supported, but using a parameterized class won't work as expected:

    === "Python 3.9 and above"

        ```python {upgrade="skip"}
        from typing import Generic, TypeVar

        from pydantic.dataclasses import dataclass

        T = TypeVar('T')


        @dataclass
        class Foo(Generic[T]):
            f: T


        Foo[int](f='not_an_int')  # (1)!
        #> Foo(f='not_an_int')
        ```

        1. Unlike [generic Pydantic models](./models.md#generic-models), `Foo[int]` is a [generic alias][types-genericalias] and not a proper type object.
           As such, Pydantic currently performs no validation.

    === "Python 3.12 and above (new syntax)"

        ```python {requires="3.12" upgrade="skip" lint="skip"}
        from pydantic.dataclasses import dataclass


        @dataclass
        class Foo[T]:
            f: T


        Foo[int](f='not_an_int')  # (1)!
        #> Foo(f='not_an_int')
        ```

        1. Unlike [generic Pydantic models](./models.md#generic-models), `Foo[int]` is a [generic alias][types-genericalias] and not a proper type object.
           As such, Pydantic currently performs no validation.

    Instead, you can wrap the `Foo[int]` parameterized class with a [`TypeAdapter`][pydantic.type_adapter.TypeAdapter].

You can use both the Pydantic's [`Field()`][pydantic.Field] and the stdlib's [`field()`][dataclasses.field] functions:

```python
import dataclasses
from typing import Optional

from pydantic import Field
from pydantic.dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str = 'John Doe'
    friends: list[int] = dataclasses.field(default_factory=lambda: [0])
    age: Optional[int] = dataclasses.field(
        default=None,
        metadata={'title': 'The age of the user', 'description': 'do not lie!'},
    )
    height: Optional[int] = Field(
        default=None, title='The height in cm', ge=50, le=300
    )


user = User(id='42', height='250')
print(user)
#> User(id=42, name='John Doe', friends=[0], age=None, height=250)
```

The Pydantic [`@dataclass`][pydantic.dataclasses.dataclass] decorator accepts the same arguments as the standard decorator,
with the addition of a `config` parameter.

## Dataclass config

If you want to modify the configuration like you would with a [`BaseModel`][pydantic.BaseModel], you have two options:

* Use the `config` parameter of the decorator.
* Define the configuration with the `__pydantic_config__` attribute.

```python
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


# Option 1 -- using the decorator argument:
@dataclass(config=ConfigDict(validate_assignment=True))  # (1)!
class MyDataclass1:
    a: int


# Option 2 -- using an attribute:
@dataclass
class MyDataclass2:
    a: int

    __pydantic_config__ = ConfigDict(validate_assignment=True)
```

1. You can read more about `validate_assignment` in the [API reference][pydantic.config.ConfigDict.validate_assignment].

## Rebuilding dataclass schema

The [`rebuild_dataclass()`][pydantic.dataclasses.rebuild_dataclass] function can be used to rebuild the core schema of the dataclass.
See the [rebuilding model schema](./models.md#rebuilding-model-schema) section for more details.

## Stdlib dataclasses and Pydantic dataclasses

### Inherit from stdlib dataclasses

Stdlib dataclasses (nested or not) can also be inherited and Pydantic will automatically validate
all the inherited fields.

```python
import dataclasses

import pydantic


@dataclasses.dataclass
class Z:
    z: int


@dataclasses.dataclass
class Y(Z):
    y: int = 0


@pydantic.dataclasses.dataclass
class X(Y):
    x: int = 0


foo = X(x=b'1', y='2', z='3')
print(foo)
#> X(z=3, y=2, x=1)

try:
    X(z='pika')
except pydantic.ValidationError as e:
    print(e)
    """
    1 validation error for X
    z
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='pika', input_type=str]
    """
```

The decorator can also be applied directly on a stdlib dataclass, in which case a new subclass will be created:

```python
import dataclasses

import pydantic


@dataclasses.dataclass
class A:
    a: int


PydanticA = pydantic.dataclasses.dataclass(A)
print(PydanticA(a='1'))
#> A(a=1)
```

### Usage of stdlib dataclasses with `BaseModel`

When a standard library dataclass is used within a Pydantic model, a Pydantic dataclass or a [`TypeAdapter`][pydantic.TypeAdapter],
validation will be applied (and the [configuration](#dataclass-config) stays the same). This means that using a stdlib or a Pydantic
dataclass as a field annotation is functionally equivalent.

```python
import dataclasses
from typing import Optional

from pydantic import BaseModel, ConfigDict, ValidationError


@dataclasses.dataclass(frozen=True)
class User:
    name: str


class Foo(BaseModel):
    # Required so that pydantic revalidates the model attributes:
    model_config = ConfigDict(revalidate_instances='always')

    user: Optional[User] = None


# nothing is validated as expected:
user = User(name=['not', 'a', 'string'])
print(user)
#> User(name=['not', 'a', 'string'])


try:
    Foo(user=user)
except ValidationError as e:
    print(e)
    """
    1 validation error for Foo
    user.name
      Input should be a valid string [type=string_type, input_value=['not', 'a', 'string'], input_type=list]
    """

foo = Foo(user=User(name='pika'))
try:
    foo.user.name = 'bulbi'
except dataclasses.FrozenInstanceError as e:
    print(e)
    #> cannot assign to field 'name'
```

### Using custom types

As said above, validation is applied on standard library dataclasses. If you make use
of custom types, you will get an error when trying to refer to the dataclass. To circumvent
the issue, you can set the [`arbitrary_types_allowed`][pydantic.ConfigDict.arbitrary_types_allowed]
configuration value on the dataclass:

```python
import dataclasses

from pydantic import BaseModel, ConfigDict
from pydantic.errors import PydanticSchemaGenerationError


class ArbitraryType:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'ArbitraryType(value={self.value!r})'


@dataclasses.dataclass
class DC:
    a: ArbitraryType
    b: str


# valid as it is a stdlib dataclass without validation:
my_dc = DC(a=ArbitraryType(value=3), b='qwe')

try:

    class Model(BaseModel):
        dc: DC
        other: str

    # invalid as dc is now validated with pydantic, and ArbitraryType is not a known type
    Model(dc=my_dc, other='other')

except PydanticSchemaGenerationError as e:
    print(e.message)
    """
    Unable to generate pydantic-core schema for <class '__main__.ArbitraryType'>. Set `arbitrary_types_allowed=True` in the model_config to ignore this error or implement `__get_pydantic_core_schema__` on your type to fully support it.

    If you got this error by calling handler(<some type>) within `__get_pydantic_core_schema__` then you likely need to call `handler.generate_schema(<some type>)` since we do not call `__get_pydantic_core_schema__` on `<some type>` otherwise to avoid infinite recursion.
    """


# valid as we set arbitrary_types_allowed=True, and that config pushes down to the nested vanilla dataclass
class Model(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    dc: DC
    other: str


m = Model(dc=my_dc, other='other')
print(repr(m))
#> Model(dc=DC(a=ArbitraryType(value=3), b='qwe'), other='other')
```

### Checking if a dataclass is a Pydantic dataclass

Pydantic dataclasses are still considered dataclasses, so using [`dataclasses.is_dataclass()`][dataclasses.is_dataclass]
will return `True`. To check if a type is specifically a Pydantic dataclass you can use the
[`is_pydantic_dataclass()`][pydantic.dataclasses.is_pydantic_dataclass] function.

```python
import dataclasses

import pydantic


@dataclasses.dataclass
class StdLibDataclass:
    id: int


PydanticDataclass = pydantic.dataclasses.dataclass(StdLibDataclass)

print(dataclasses.is_dataclass(StdLibDataclass))
#> True
print(pydantic.dataclasses.is_pydantic_dataclass(StdLibDataclass))
#> False

print(dataclasses.is_dataclass(PydanticDataclass))
#> True
print(pydantic.dataclasses.is_pydantic_dataclass(PydanticDataclass))
#> True
```

## Validators and initialization hooks

Validators also work with Pydantic dataclasses:

```python
from pydantic import field_validator
from pydantic.dataclasses import dataclass


@dataclass
class DemoDataclass:
    product_id: str  # should be a five-digit string, may have leading zeros

    @field_validator('product_id', mode='before')
    @classmethod
    def convert_int_serial(cls, v):
        if isinstance(v, int):
            v = str(v).zfill(5)
        return v


print(DemoDataclass(product_id='01234'))
#> DemoDataclass(product_id='01234')
print(DemoDataclass(product_id=2468))
#> DemoDataclass(product_id='02468')
```

<!-- markdownlint-disable-next-line strong-style -->
The dataclass [`__post_init__()`][dataclasses.__post_init__] method is also supported, and will
be called between the calls to *before* and *after* model validators.

??? example

    ```python
    from pydantic_core import ArgsKwargs
    from typing_extensions import Self

    from pydantic import model_validator
    from pydantic.dataclasses import dataclass


    @dataclass
    class Birth:
        year: int
        month: int
        day: int


    @dataclass
    class User:
        birth: Birth

        @model_validator(mode='before')
        @classmethod
        def before(cls, values: ArgsKwargs) -> ArgsKwargs:
            print(f'First: {values}')  # (1)!
            """
            First: ArgsKwargs((), {'birth': {'year': 1995, 'month': 3, 'day': 2}})
            """
            return values

        @model_validator(mode='after')
        def after(self) -> Self:
            print(f'Third: {self}')
            #> Third: User(birth=Birth(year=1995, month=3, day=2))
            return self

        def __post_init__(self):
            print(f'Second: {self.birth}')
            #> Second: Birth(year=1995, month=3, day=2)


    user = User(**{'birth': {'year': 1995, 'month': 3, 'day': 2}})
    ```

    1. Unlike Pydantic models, the `values` parameter is of type [`ArgsKwargs`][pydantic_core.ArgsKwargs]
