The behaviour of Pydantic can be controlled via a variety of configuration values, documented
on the [`ConfigDict`][pydantic.ConfigDict] class. This page describes how configuration can be
specified for Pydantic's supported types.

## Configuration on Pydantic models

On Pydantic models, configuration can be specified in two ways:

* Using the [`model_config`][pydantic.BaseModel.model_config] class attribute:

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

    !!! note
        In Pydantic V1, the `Config` class was used. This is still supported, but **deprecated**.

* Using class arguments:

    ```python
    from pydantic import BaseModel


    class Model(BaseModel, frozen=True):
        a: str
    ```

  Unlike the [`model_config`][pydantic.BaseModel.model_config] class attribute,
  static type checkers will recognize class arguments. For `frozen`, any instance
  mutation will be flagged as an type checking error.

## Configuration on Pydantic dataclasses

[Pydantic dataclasses](./dataclasses.md) also support configuration (read more in the
[dedicated section](./dataclasses.md#dataclass-config)).

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

[Type adapters](./type_adapter.md) (using the [`TypeAdapter`][pydantic.TypeAdapter] class) support configuration,
by providing the `config` argument.

```python
from pydantic import ConfigDict, TypeAdapter

ta = TypeAdapter(list[str], config=ConfigDict(coerce_numbers_to_str=True))

print(ta.validate_python([1, 2]))
#> ['1', '2']
```

## Configuration on other supported types

If you are using [standard library dataclasses][dataclasses] or [`TypedDict`][typing.TypedDict] classes,
the configuration can be set in two ways:

* Using the `__pydantic_config__` class attribute:

    ```python
    from dataclasses import dataclass

    from pydantic import ConfigDict


    @dataclass
    class User:
        __pydantic_config__ = ConfigDict(strict=True)

        id: int
        name: str = 'John Doe'
    ```

* Using the [`@with_config`][pydantic.config.with_config] decorator (this avoids static type checking errors with
  [`TypedDict`][typing.TypedDict]):

    ```python
    from typing_extensions import TypedDict

    from pydantic import ConfigDict, with_config


    @with_config(ConfigDict(str_to_lower=True))
    class Model(TypedDict):
        x: str
    ```

## Configuration on the `@validate_call` decorator

The [`@validate_call`](./validation_decorator.md) also supports setting custom configuration. See the
[dedicated section](./validation_decorator.md#custom-configuration) for more details.

## Change behaviour globally

If you wish to change the behaviour of Pydantic globally, you can create your own custom parent class
with a custom configuration, as the configuration is inherited:

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

!!! warning
    If your model inherits from multiple bases, Pydantic currently *doesn't* follow the
    [MRO]. For more details, see [this issue](https://github.com/pydantic/pydantic/issues/9992).

    [MRO]: https://docs.python.org/3/glossary.html#term-method-resolution-order

## Configuration propagation

When using types that support configuration as field annotations, configuration may not be propagated:

* For Pydantic models and dataclasses, configuration will *not* be propagated, each model has its own
  "configuration boundary":

    ```python
    from pydantic import BaseModel, ConfigDict


    class User(BaseModel):
        name: str


    class Parent(BaseModel):
        user: User

        model_config = ConfigDict(str_to_lower=True)


    print(Parent(user={'name': 'JOHN'}))
    #> user=User(name='JOHN')
    ```

* For stdlib types (dataclasses and typed dictionaries), configuration will be propagated, unless
  the type has its own configuration set:

    ```python
    from dataclasses import dataclass

    from pydantic import BaseModel, ConfigDict, with_config


    @dataclass
    class UserWithoutConfig:
        name: str


    @dataclass
    @with_config(str_to_lower=False)
    class UserWithConfig:
        name: str


    class Parent(BaseModel):
        user_1: UserWithoutConfig
        user_2: UserWithConfig

        model_config = ConfigDict(str_to_lower=True)


    print(Parent(user_1={'name': 'JOHN'}, user_2={'name': 'JOHN'}))
    #> user_1=UserWithoutConfig(name='john') user_2=UserWithConfig(name='JOHN')
    ```
