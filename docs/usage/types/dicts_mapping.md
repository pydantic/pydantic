# Dicts and Mapping Types

`dict`
: `dict(v)` is used to attempt to convert a dictionary;
  see `typing.Dict` below for sub-type constraints

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: dict


m = Model(x={'foo': 1})
print(m.model_dump())
#> {'x': {'foo': 1}}

try:
    Model(x='test')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    x
      Input should be a valid dictionary [type=dict_type, input_value='test', input_type=str]
    """
```

`typing.Dict`

```py
from typing import Dict

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    x: Dict[str, int]


m = Model(x={'foo': 1})
print(m.model_dump())
#> {'x': {'foo': 1}}

try:
    Model(x={'foo': '1'})
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    x
      Input should be a valid dictionary [type=dict_type, input_value='test', input_type=str]
    """
```

### TypedDict

!!! note
    This is a new feature of the Python standard library as of Python 3.8.
    Prior to Python 3.8, it requires the [typing-extensions](https://pypi.org/project/typing-extensions/) package.
    But required and optional fields are properly differentiated only since Python 3.9.
    We therefore recommend using [typing-extensions](https://pypi.org/project/typing-extensions/) with Python 3.8 as well.

Same as `dict` but Pydantic will validate the dictionary since keys are annotated.

```py
from typing import Optional

from typing_extensions import TypedDict

from pydantic import BaseModel, ConfigDict, ValidationError


# `total=False` means keys are non-required
class UserIdentity(TypedDict, total=False):
    name: Optional[str]
    surname: str


class User(TypedDict):
    __pydantic_config__ = ConfigDict(extra='forbid')  # type: ignore

    identity: UserIdentity
    age: int


class Model(BaseModel):
    u: User


print(Model(u={'identity': {'name': 'Smith', 'surname': 'John'}, 'age': 37}))
#> u={'identity': {'name': 'Smith', 'surname': 'John'}, 'age': 37}

print(Model(u={'identity': {'name': None, 'surname': 'John'}, 'age': 37}))
#> u={'identity': {'name': None, 'surname': 'John'}, 'age': 37}

print(Model(u={'identity': {}, 'age': 37}))
#> u={'identity': {}, 'age': 37}


try:
    Model(u={'identity': {'name': ['Smith'], 'surname': 'John'}, 'age': 24})
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
