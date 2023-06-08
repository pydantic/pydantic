If you don't want to use _pydantic_'s `BaseModel` you can instead get the same data validation on standard
[dataclasses](https://docs.python.org/3/library/dataclasses.html) (introduced in Python 3.7).

```py
from datetime import datetime

from pydantic.dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str = 'John Doe'
    signup_ts: datetime = None


user = User(id='42', signup_ts='2032-06-21T12:00')
print(user)
#> User(id=42, name='John Doe', signup_ts=datetime.datetime(2032, 6, 21, 12, 0))
```

!!! note
    Keep in mind that `pydantic.dataclasses.dataclass` is **not** a replacement for `pydantic.BaseModel` (with a small
    difference in how [initialization hooks](#initialize-hooks) work). `pydantic.dataclasses.dataclass` provides a
    similar functionality to `dataclasses.dataclass` with the addition of Pydantic validation. There are cases where
    subclassing `pydantic.BaseModel` is the better choice.

    For more information and discussion see
    [pydantic/pydantic#710](https://github.com/pydantic/pydantic/issues/710).

You can use all the standard _pydantic_ field types. Note, however, that arguments passed to constructor will be copied in order to perform validation and, where necessary coercion.

The schema can be accessed by [TypeAdapter](models.md#using-pydantic-without-creating-a-basemodel).
Also, fields that require a `default_factory` can be specified by either a `pydantic.Field` or a `dataclasses.field`.

```py
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
        metadata=dict(title='The age of the user', description='do not lie!'),
    )
    height: Optional[int] = Field(None, title='The height in cm', ge=50, le=300)


user = User(id='42')
print(TypeAdapter(User).json_schema())
"""
{
    'properties': {
        'age': {
            'anyOf': [{'type': 'integer'}, {'type': 'null'}],
            'default': None,
            'description': 'do not lie!',
            'title': 'The age of the user',
        },
        'friends': {
            'default': [0],
            'items': {'type': 'integer'},
            'title': 'Friends',
            'type': 'array',
        },
        'height': {
            'anyOf': [
                {'maximum': 300, 'minimum': 50, 'type': 'integer'},
                {'type': 'null'},
            ],
            'default': None,
            'title': 'The height in cm',
        },
        'id': {'title': 'Id', 'type': 'integer'},
        'name': {'default': 'John Doe', 'title': 'Name', 'type': 'string'},
    },
    'required': ['id'],
    'title': 'User',
    'type': 'object',
}
"""
```

`pydantic.dataclasses.dataclass`'s arguments are the same as the standard decorator, except one extra
keyword argument `config` which has the same meaning as [model_config](model_config.md).

!!! warning
    After v1.2, [The Mypy plugin](/mypy/) must be installed to type check _pydantic_ dataclasses.

For more information about combining validators with dataclasses, see
[dataclass validators](validators.md#dataclass-validators).

## Dataclass Config

If you want to modify the `config` like you would with a `BaseModel`, you have two options:

```py
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


# Option 1 - use directly a dict
# Note: `mypy` will still raise typo error
@dataclass(config=dict(validate_assignment=True))
class MyDataclass1:
    a: int


# Option 2 - use `ConfigDict`
# (same as before at runtime since it's a `TypedDict` but with intellisense)
@dataclass(config=ConfigDict(validate_assignment=True))
class MyDataclass2:
    a: int
```

!!! warning
    After v1.10, _pydantic_ dataclasses support `Config.extra` but some default behaviour of stdlib dataclasses
    may prevail. For example, when `print`ing a _pydantic_ dataclass with allowed extra fields, it will still
    use the `__str__` method of stdlib dataclass and show only the required fields.
    This may be improved further in the future.

## Nested dataclasses

Nested dataclasses are supported both in dataclasses and normal models.

```py
from pydantic import AnyUrl
from pydantic.dataclasses import dataclass


@dataclass
class NavbarButton:
    href: AnyUrl


@dataclass
class Navbar:
    button: NavbarButton


navbar = Navbar(button={'href': 'https://example.com'})
print(navbar)
#> Navbar(button=NavbarButton(href=Url('https://example.com/')))
```

Dataclasses attributes can be populated by tuples, dictionaries or instances of the dataclass itself.

## Stdlib dataclasses and _pydantic_ dataclasses

### Inherit from stdlib dataclasses

Stdlib dataclasses (nested or not) can also be inherited and _pydantic_ will automatically validate
all the inherited fields.

```py
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

### Use of stdlib dataclasses with `BaseModel`

Bear in mind that stdlib dataclasses (nested or not) are **automatically converted** into _pydantic_
dataclasses when mixed with `BaseModel`! Furthermore the generated _pydantic_ dataclass will have
the **exact same configuration** (`order`, `frozen`, ...) as the original one.

```py
import dataclasses
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ValidationError


@dataclasses.dataclass(frozen=True)
class User:
    name: str


@dataclasses.dataclass
class File:
    filename: str
    last_modification_time: Optional[datetime] = None


class Foo(BaseModel):
    file: File
    user: Optional[User] = None


file = File(
    filename=['not', 'a', 'string'],
    last_modification_time='2020-01-01T00:00',
)  # nothing is validated as expected
print(file)
#> File(filename=['not', 'a', 'string'], last_modification_time='2020-01-01T00:00')

try:
    Foo(file=file)
except ValidationError as e:
    print(e)
    """
    1 validation error for Foo
    file.filename
      Input should be a valid string [type=string_type, input_value=['not', 'a', 'string'], input_type=list]
    """

foo = Foo(file=File(filename='myfile'), user=User(name='pika'))
try:
    foo.user.name = 'bulbi'
except dataclasses.FrozenInstanceError as e:
    print(e)
    #> cannot assign to field 'name'
```

### Use custom types

Since stdlib dataclasses are automatically converted to add validation using
custom types may cause some unexpected behaviour.
In this case you can simply add `arbitrary_types_allowed` in the config!

```py
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


# valid as it is a builtin dataclass without validation
my_dc = DC(a=ArbitraryType(value=3), b='qwe')

try:

    class Model(BaseModel):
        dc: DC
        other: str

    Model(dc=my_dc, other='other')
except PydanticSchemaGenerationError as e:  # invalid as it is now a pydantic dataclass
    print(e.message)
    """
    Unable to generate pydantic-core schema for <class '__main__.ArbitraryType'>. Set `arbitrary_types_allowed=True` in the model_config to ignore this error or implement `__get_pydantic_core_schema__` on your type to fully support it.

    If you got this error by calling handler(<some type>) within `__get_pydantic_core_schema__` then you likely need to call `handler.generate_schema(<some type>)` since we do not call `__get_pydantic_core_schema__` on `<some type>` otherwise to avoid infinite recursion.
    """


class Model(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    dc: DC
    other: str


m = Model(dc=my_dc, other='other')
print(repr(m))
#> Model(dc=DC(a=ArbitraryType(value=3), b='qwe'), other='other')
```

## Initialize hooks

When you initialize a dataclass, it is possible to execute code *before* or *after* validation
with the help of `model_validator` decorator.

```py
from typing import Any, Dict

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
    def pre_root(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        print(values)
        #> ArgsKwargs((), {'birth': {'year': 1995, 'month': 3, 'day': 2}})
        return values

    @model_validator(mode='after')
    def post_root(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        print(values)
        #> User(birth=Birth(year=1995, month=3, day=2))
        return values

    def __post_init__(self):
        print(self.birth)
        #> Birth(year=1995, month=3, day=2)


user = User(**{'birth': {'year': 1995, 'month': 3, 'day': 2}})
```

```py requires="3.8"
from dataclasses import InitVar
from pathlib import Path
from typing import Optional

from pydantic.dataclasses import dataclass


@dataclass
class PathData:
    path: Path
    base_path: InitVar[Optional[Path]]

    def __post_init__(self, base_path):
        print(f'Received path={self.path!r}, base_path={base_path!r}')
        #> Received path=PosixPath('world'), base_path=PosixPath('/hello')
        if base_path is not None:
            self.path = base_path / self.path


path_data = PathData('world', base_path='/hello')
# Received path='world', base_path='/hello'
assert path_data.path == Path('/hello/world')
```

### Difference with stdlib dataclasses

Note that the `dataclasses.dataclass` from Python stdlib implements only the `__post_init__` method since it doesn't run a validation step.

When substituting usage of `dataclasses.dataclass` with `pydantic.dataclasses.dataclass`, it is recommended to move the code executed in the `__post_init__` to
methods decorated with `model_validator`.

## JSON dumping

_Pydantic_ dataclasses do not feature a `.model_dump_json()` function. To dump them as JSON, you will need to
make use of the [RootModel](models.md#custom-root-types) as follows:

```py output="json"
import dataclasses
from typing import List

from pydantic import RootModel
from pydantic.dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str = 'John Doe'
    friends: List[int] = dataclasses.field(default_factory=lambda: [0])


user = User(id='42')
print(RootModel[User](User(id='42')).model_dump_json(indent=4))
"""
{
    "id": 42,
    "name": "John Doe",
    "friends": [
        0
    ]
}
"""
```
