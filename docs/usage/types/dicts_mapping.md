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

[TypedDict](https://docs.python.org/3/library/typing.html#typing.TypedDict) declares a dictionary type that expects all of
its instances to have a certain set of keys, where each key is associated with a value of a consistent type.

It is same as `dict` but Pydantic will validate the dictionary since keys are annotated.

```py
from typing_extensions import TypedDict

from pydantic import TypeAdapter, ValidationError


class User(TypedDict):
    name: str
    id: int


ta = TypeAdapter(User)

print(ta.validate_python({'name': 'foo', 'id': 1}))
#> {'name': 'foo', 'id': 1}

try:
    ta.validate_python({'name': 'foo'})
except ValidationError as e:
    print(e)
    """
    1 validation error for typed-dict
    id
      Field required [type=missing, input_value={'name': 'foo'}, input_type=dict]
    """
```

You can define `__pydantic_config__` to change the model inherited from `TypedDict`.
See [Model Config](../model_config.md) for more details.

```py
from typing import Optional

from typing_extensions import TypedDict

from pydantic import ConfigDict, TypeAdapter, ValidationError


# `total=False` means keys are non-required
class UserIdentity(TypedDict, total=False):
    name: Optional[str]
    surname: str


class User(TypedDict):
    __pydantic_config__ = ConfigDict(extra='forbid')

    identity: UserIdentity
    age: int


ta = TypeAdapter(User)

print(
    ta.validate_python(
        {'identity': {'name': 'Smith', 'surname': 'John'}, 'age': 37}
    )
)
#> {'identity': {'name': 'Smith', 'surname': 'John'}, 'age': 37}

print(
    ta.validate_python(
        {'identity': {'name': None, 'surname': 'John'}, 'age': 37}
    )
)
#> {'identity': {'name': None, 'surname': 'John'}, 'age': 37}

print(ta.validate_python({'identity': {}, 'age': 37}))
#> {'identity': {}, 'age': 37}


try:
    ta.validate_python(
        {'identity': {'name': ['Smith'], 'surname': 'John'}, 'age': 24}
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for typed-dict
    identity.name
      Input should be a valid string [type=string_type, input_value=['Smith'], input_type=list]
    """

try:
    ta.validate_python(
        {
            'identity': {'name': 'Smith', 'surname': 'John'},
            'age': '37',
            'email': 'john.smith@me.com',
        }
    )
except ValidationError as e:
    print(e)
    """
    1 validation error for typed-dict
    email
      Extra inputs are not permitted [type=extra_forbidden, input_value='john.smith@me.com', input_type=str]
    """
```
