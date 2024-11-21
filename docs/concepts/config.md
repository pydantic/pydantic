Behaviour of Pydantic can be controlled via the [`BaseModel.model_config`][pydantic.BaseModel.model_config],
and as an argument to [`TypeAdapter`][pydantic.TypeAdapter].

!!! note
    Before **v2.0**, the `Config` class was used. This is still supported, but **deprecated**.

```python
from pydantic import BaseModel, ConfigDict, ValidationError


class Model(BaseModel):
    model_config = ConfigDict(str_max_length=10)

    v: str


try:
    m = Model(v='x' * 20)
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    v
      String should have at most 10 characters [type=string_too_long, input_value='xxxxxxxxxxxxxxxxxxxx', input_type=str]
    """
```

Also, you can specify config options as model class kwargs:
```python
from pydantic import BaseModel, ValidationError


class Model(BaseModel, extra='forbid'):  # (1)!
    a: str


try:
    Model(a='spam', b='oh no')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    b
      Extra inputs are not permitted [type=extra_forbidden, input_value='oh no', input_type=str]
    """
```

1. See the [Extra Attributes](models.md#extra-fields) section for more details.

Similarly, if using the [`@dataclass`][pydantic.dataclasses] decorator from Pydantic:
```python
from datetime import datetime

from pydantic import ConfigDict, ValidationError
from pydantic.dataclasses import dataclass

config = ConfigDict(str_max_length=10, validate_assignment=True)


@dataclass(config=config)
class User:
    id: int
    name: str = 'John Doe'
    signup_ts: datetime = None


user = User(id='42', signup_ts='2032-06-21T12:00')
try:
    user.name = 'x' * 20
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    name
      String should have at most 10 characters [type=string_too_long, input_value='xxxxxxxxxxxxxxxxxxxx', input_type=str]
    """
```

## Configuration with `dataclass` from the standard library or `TypedDict`

If using the `dataclass` from the standard library or `TypedDict`, you should use `__pydantic_config__` instead.

```python
from dataclasses import dataclass
from datetime import datetime

from pydantic import ConfigDict


@dataclass
class User:
    __pydantic_config__ = ConfigDict(strict=True)

    id: int
    name: str = 'John Doe'
    signup_ts: datetime = None
```

Alternatively, the [`with_config`][pydantic.config.with_config] decorator can be used to comply with type checkers.

```python
from typing_extensions import TypedDict

from pydantic import ConfigDict, with_config


@with_config(ConfigDict(str_to_lower=True))
class Model(TypedDict):
    x: str
```

## Change behaviour globally

If you wish to change the behaviour of Pydantic globally, you can create your own custom `BaseModel`
with custom `model_config` since the config is inherited:

```python
from pydantic import BaseModel, ConfigDict


class Parent(BaseModel):
    model_config = ConfigDict(extra='allow')


class Model(Parent):
    x: str


m = Model(x='foo', y='bar')
print(m.model_dump())
#> {'x': 'foo', 'y': 'bar'}
```

If you add a `model_config` to the `Model` class, it will _merge_ with the `model_config` from `Parent`:

```python
from pydantic import BaseModel, ConfigDict


class Parent(BaseModel):
    model_config = ConfigDict(extra='allow')


class Model(Parent):
    model_config = ConfigDict(str_to_lower=True)  # (1)!

    x: str


m = Model(x='FOO', y='bar')
print(m.model_dump())
#> {'x': 'foo', 'y': 'bar'}
print(m.model_config)
#> {'extra': 'allow', 'str_to_lower': True}
```
