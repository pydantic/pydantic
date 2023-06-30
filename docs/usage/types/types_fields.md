---
description: Support for types with fields including NamedTuple and TypedDict.
---

Pydantic supports four types with fields:

* [`BaseModel`](../models.md)
* [dataclasses](../dataclasses.md)
* [`NamedTuple`](#namedtuple)
* [`TypedDict`](#typeddict)

### NamedTuple

```py
from typing import NamedTuple

from pydantic import BaseModel, ValidationError


class Point(NamedTuple):
    x: int
    y: int


class Model(BaseModel):
    p: Point


print(Model(p=('1', '2')))
#> p=Point(x=1, y=2)

try:
    Model(p=('1.3', '2'))
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    p.0
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='1.3', input_type=str]
    """
```

### TypedDict

!!! note
    This is a new feature of the Python standard library as of Python 3.8.
    Prior to Python 3.8, it requires the [typing-extensions](https://pypi.org/project/typing-extensions/) package.
    But required and optional fields are properly differentiated only since Python 3.9.
    We therefore recommend using [typing-extensions](https://pypi.org/project/typing-extensions/) with Python 3.8 as well.


```py
from typing_extensions import TypedDict

from pydantic import BaseModel, ConfigDict, ValidationError


# `total=False` means keys are non-required
class UserIdentity(TypedDict, total=False):
    name: str
    surname: str


class User(TypedDict):
    __pydantic_config__ = ConfigDict(extra='forbid')

    identity: UserIdentity
    age: int


class Model(BaseModel):
    u: User


print(Model(u={'identity': {'name': 'Smith', 'surname': 'John'}, 'age': '37'}))
#> u={'identity': {'name': 'Smith', 'surname': 'John'}, 'age': 37}

print(Model(u={'identity': {'surname': 'John'}, 'age': '37'}))
#> u={'identity': {'surname': 'John'}, 'age': 37}

print(Model(u={'identity': {}, 'age': '37'}))
#> u={'identity': {}, 'age': 37}


try:
    Model(u={'identity': {'name': ['Smith'], 'surname': 'John'}, 'age': '24'})
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    u.identity.name
      Input should be a valid string [type=string_type, input_value=['Smith'], input_type=list]
    """

try:
    Model(
        u={
            'identity': {'name': 'Smith', 'surname': 'John'},
            'age': '37',
            'email': 'john.smith@me.com',
        }
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    u.email
      Extra inputs are not permitted [type=extra_forbidden, input_value='john.smith@me.com', input_type=str]
    """
```
