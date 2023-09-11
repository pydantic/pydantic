??? api "API Documentation"
    [`pydantic.config.ConfigDict`][pydantic.config.ConfigDict]<br>

Behaviour of Pydantic can be controlled via the [`BaseModel.model_config`][pydantic.BaseModel.model_config],
and as an argument to [`TypeAdapter`][pydantic.TypeAdapter].

!!! note
    Before **v2.0**, the `Config` class was used. This is still supported, but deprecated.

```py
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
```py
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

1. See the [Extra Attributes](#extra-attributes) section for more details.

Similarly, if using the `@dataclass` decorator from _pydantic_:
```py
from datetime import datetime

from pydantic import ConfigDict, ValidationError
from pydantic.dataclasses import dataclass

config = ConfigDict(str_max_length=10, validate_assignment=True)


@dataclass(config=config)  # (1)!
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


1. If using the `dataclass` from the standard library or `TypedDict`, you should use `__pydantic_config__` instead.
   See:

    ```py
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

## Options

See the [`ConfigDict` API documentation](../api/config.md#pydantic.config.ConfigDict) for the full list of settings.

## Change behaviour globally

If you wish to change the behaviour of Pydantic globally, you can create your own custom `BaseModel`
with custom `model_config` since the config is inherited:

```py
from pydantic import BaseModel, ConfigDict


class Parent(BaseModel):
    model_config = ConfigDict(extra='allow')


class Model(Parent):
    x: str


m = Model(x='foo', y='bar')
print(m.model_dump())
#> {'x': 'foo', 'y': 'bar'}
```

1. Since `Parent` is a subclass of `BaseModel`, it will inherit the `model_config` attribute.
   This means that `Model` will have `extra='allow'` by default.

If you add a `model_config` to the `Model` class, it will _merge_ with the `model_config` from `Parent`:

```py
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

## Alias Precedence

If you specify an `alias` on the `Field`, it will take precedence over the generated alias by default:

```py
from pydantic import BaseModel, ConfigDict, Field


def to_camel(string: str) -> str:
    return ''.join(word.capitalize() for word in string.split('_'))


class Voice(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    name: str
    language_code: str = Field(alias='lang')


voice = Voice(Name='Filiz', lang='tr-TR')
print(voice.language_code)
#> tr-TR
print(voice.model_dump(by_alias=True))
#> {'Name': 'Filiz', 'lang': 'tr-TR'}
```

### Alias Priority

You may set `alias_priority` on a field to change this behavior:

* `alias_priority=2` the alias will *not* be overridden by the alias generator.
* `alias_priority=1` the alias *will* be overridden by the alias generator.
* `alias_priority` not set, the alias will be overridden by the alias generator.

The same precedence applies to `validation_alias` and `serialization_alias`.
See more about the different field aliases under [field aliases](fields.md#field-aliases).

## Strict Mode

By default, Pydantic attempts to coerce values to the correct type, when possible.

There are situations in which you may want to disable this behavior, and instead raise an error if a value's type
does not match the field's type annotation.

To configure strict mode for all fields on a model, you can
[set `model_config = ConfigDict(strict=True)`](../api/config.md#pydantic.config.ConfigDict) on the model.


```py
from pydantic import BaseModel, ConfigDict


class Model(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    age: int
```

See [Strict Mode](strict_mode.md) for more details.

See the [Conversion Table](conversion_table.md) for more details on how Pydantic converts data in both strict and lax
modes.
