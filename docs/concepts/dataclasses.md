??? api "API Documentation"
    [`pydantic.dataclasses.dataclass`][pydantic.dataclasses.dataclass]<br>

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

    There are cases where subclassing using Pydantic models is the better choice.

    For more information and discussion see
    [pydantic/pydantic#710](https://github.com/pydantic/pydantic/issues/710).

Similarities between Pydantic dataclasses and models include support for:

* [Configuration](#dataclass-config) support
* [Nested](./models.md#nested-models) classes
* [Generics](./models.md#generic-models)

Some differences between Pydantic dataclasses and models include:

*  [validators](#validators-and-initialization-hooks)
*  The behavior with the [`extra`][pydantic.ConfigDict.extra] configuration value

Similarly to Pydantic models, arguments used to instantiate the dataclass are [copied](./models.md#attribute-copies).

To make use of the [various methods](./models.md#model-methods-and-properties) to validate, dump and generate a JSON Schema,
you can wrap the dataclass with a [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] and make use of its methods.

You can use both the Pydantic's [`Field()`][pydantic.Field] and the stdlib's [`field()`][dataclasses.field] functions:

```python
import dataclasses
from typing import List, Optional

from pydantic import Field, TypeAdapter
from pydantic.dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str = 'John Doe'
    friends: List[int] = dataclasses.field(default_factory=lambda: [0])
    age: Optional[int] = dataclasses.field(
        default=None,
        metadata={'title': 'The age of the user', 'description': 'do not lie!'},
    )
    height: Optional[int] = Field(None, title='The height in cm', ge=50, le=300)


user = User(id='42')
print(TypeAdapter(User).json_schema())
"""
{
    'properties': {
        'id': {'title': 'Id', 'type': 'integer'},
        'name': {'default': 'John Doe', 'title': 'Name', 'type': 'string'},
        'friends': {
            'items': {'type': 'integer'},
            'title': 'Friends',
            'type': 'array',
        },
        'age': {
            'anyOf': [{'type': 'integer'}, {'type': 'null'}],
            'default': None,
            'description': 'do not lie!',
            'title': 'The age of the user',
        },
        'height': {
            'anyOf': [
                {'maximum': 300, 'minimum': 50, 'type': 'integer'},
                {'type': 'null'},
            ],
            'default': None,
            'title': 'The height in cm',
        },
    },
    'required': ['id'],
    'title': 'User',
    'type': 'object',
}
"""
```

The Pydantic `@dataclass` decorator accepts the same arguments as the standard decorator, with the addition
of a `config` parameter.

## Dataclass config

If you want to modify the configuration like you would with a [`BaseModel`][pydantic.BaseModel], you have two options:

* Use the `config` argument of the decorator.
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

!!! note
    While Pydantic dataclasses support the [`extra`][pydantic.config.ConfigDict.extra] configuration value, some default
    behavior of stdlib dataclasses may prevail. For example, any extra fields present on a Pydantic dataclass with
    [`extra`][pydantic.config.ConfigDict.extra] set to `'allow'` are omitted in the dataclass' string representation.

## Rebuilding dataclass schema

The [`rebuild_dataclass()`][pydantic.dataclasses.rebuild_dataclass] can be used to rebuild the core schema of the dataclass.
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

from pydantic import BaseModel
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

except PydanticSchemaGenerationError as e:
    print(e.message)
    """
    Unable to generate pydantic-core schema for <class '__main__.ArbitraryType'>. Set `arbitrary_types_allowed=True` in the model_config to ignore this error or implement `__get_pydantic_core_schema__` on your type to fully support it.

    If you got this error by calling handler(<some type>) within `__get_pydantic_core_schema__` then you likely need to call `handler.generate_schema(<some type>)` since we do not call `__get_pydantic_core_schema__` on `<some type>` otherwise to avoid infinite recursion.
    """


@dataclasses.dataclass
class DC2:
    a: ArbitraryType
    b: str

    __pydantic_config__ = {'arbitrary_types_allowed': True}


class Model(BaseModel):
    dc: DC2
    other: str


m = Model(dc=DC2(a=ArbitraryType(value=3), b='qwe'), other='other')
print(repr(m))
#> Model(dc=DC2(a=ArbitraryType(value=3), b='qwe'), other='other')
```

### Checking if a dataclass is a Pydantic dataclass

Pydantic dataclasses are still considered dataclasses, so using [`dataclasses.is_dataclass`][] will return `True`. To check
if a type is specifically a pydantic dataclass you can use the [`is_pydantic_dataclass`][pydantic.dataclasses.is_pydantic_dataclass]
function.

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
