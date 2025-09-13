The behaviour of Pydantic can be controlled via a variety of configuration values, documented on the ConfigDict class. This page describes how configuration can be specified for Pydantic's supported types.

## Configuration on Pydantic models

On Pydantic models, configuration can be specified in two ways:

- Using the model_config class attribute:

  ```python
  from pydantic import BaseModel, ConfigDict, ValidationError


  class Model(BaseModel):
      model_config = ConfigDict(str_max_length=5)  # (1)!

      v: str


  try:
      m = Model(v='abcdef')
  except ValidationError as e:
      print(e)
      """
      1 validation error for Model
      v
        String should have at most 5 characters [type=string_too_long, input_value='abcdef', input_type=str]
      """

  ```

  1. A plain dictionary (i.e. `{'str_max_length': 5}`) can also be used.

  Note

  In Pydantic V1, the `Config` class was used. This is still supported, but **deprecated**.

- Using class arguments:

  ```python
  from pydantic import BaseModel


  class Model(BaseModel, frozen=True):
      a: str  # (1)!

  ```

  1. Unlike the model_config class attribute, static type checkers will recognize the `frozen` argument, and so any instance mutation will be flagged as an type checking error.

## Configuration on Pydantic dataclasses

[Pydantic dataclasses](../dataclasses/) also support configuration (read more in the [dedicated section](../dataclasses/#dataclass-config)).

```python
from pydantic import ConfigDict, ValidationError
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(str_max_length=10, validate_assignment=True))
class User:
    name: str


user = User(name='John Doe')
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

## Configuration on `TypeAdapter`

[Type adapters](../type_adapter/) (using the TypeAdapter class) support configuration, by providing a `config` argument.

```python
from pydantic import ConfigDict, TypeAdapter

ta = TypeAdapter(list[str], config=ConfigDict(coerce_numbers_to_str=True))

print(ta.validate_python([1, 2]))
#> ['1', '2']

```

## Configuration on other supported types

If you are using standard library dataclasses or TypedDict classes, the configuration can be set in two ways:

- Using the `__pydantic_config__` class attribute:

  ```python
  from dataclasses import dataclass

  from pydantic import ConfigDict


  @dataclass
  class User:
      __pydantic_config__ = ConfigDict(strict=True)

      id: int
      name: str = 'John Doe'

  ```

- Using the with_config decorator (this avoids static type checking errors with TypedDict):

  ```python
  from typing_extensions import TypedDict

  from pydantic import ConfigDict, with_config


  @with_config(ConfigDict(str_to_lower=True))
  class Model(TypedDict):
      x: str

  ```

## Change behaviour globally

If you wish to change the behaviour of Pydantic globally, you can create your own custom parent class with a custom configuration, as the configuration is inherited:

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

If you provide configuration to the subclasses, it will be *merged* with the parent configuration:

```python
from pydantic import BaseModel, ConfigDict


class Parent(BaseModel):
    model_config = ConfigDict(extra='allow', str_to_lower=False)


class Model(Parent):
    model_config = ConfigDict(str_to_lower=True)

    x: str


m = Model(x='FOO', y='bar')
print(m.model_dump())
#> {'x': 'foo', 'y': 'bar'}
print(Model.model_config)
#> {'extra': 'allow', 'str_to_lower': True}

```

Warning

If your model inherits from multiple bases, Pydantic currently *doesn't* follow the [MRO](https://docs.python.org/3/glossary.html#term-method-resolution-order). For more details, see [this issue](https://github.com/pydantic/pydantic/issues/9992).

## Configuration propagation

Note that when using types that support configuration as field annotations on other types, configuration will *not* be propagated. In the following example, each model has its own "configuration boundary":

```python
from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    name: str


class Parent(BaseModel):
    user: User

    model_config = ConfigDict(str_max_length=2)


print(Parent(user={'name': 'John Doe'}))
#> user=User(name='John Doe')

```
