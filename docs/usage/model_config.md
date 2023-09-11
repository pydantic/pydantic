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

## Alias Generator

If data source field names do not match your code style (e. g. CamelCase fields),
you can automatically generate aliases using `alias_generator`:

```py
from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    return ''.join(word.capitalize() for word in string.split('_'))


class Voice(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    name: str
    language_code: str


voice = Voice(Name='Filiz', LanguageCode='tr-TR')
print(voice.language_code)
#> tr-TR
print(voice.model_dump(by_alias=True))
#> {'Name': 'Filiz', 'LanguageCode': 'tr-TR'}
```

Here camel case refers to ["upper camel case"](https://en.wikipedia.org/wiki/Camel_case) aka pascal case
e.g. `CamelCase`. If you'd like instead to use lower camel case e.g. `camelCase`,
instead use the `to_lower_camel` function.

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

## Extra Attributes

You can configure how pydantic handles the attributes that are not defined in the model:

* `allow` - Allow any extra attributes.
* `forbid` - Forbid any extra attributes.
* `ignore` - Ignore any extra attributes.

The default value is `'ignore'`.

```py
from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    model_config = ConfigDict(extra='ignore')  # (1)!

    name: str


user = User(name='John Doe', age=20)  # (2)!
print(user)
#> name='John Doe'
```

1. This is the default behaviour.
2. The `age` argument is ignored.

Instead, with `extra='allow'`, the `age` argument is included:

```py
from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    model_config = ConfigDict(extra='allow')

    name: str


user = User(name='John Doe', age=20)  # (1)!
print(user)
#> name='John Doe' age=20
```

1. The `age` argument is included.

With `extra='forbid'`, an error is raised:

```py
from pydantic import BaseModel, ConfigDict, ValidationError


class User(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str


try:
    User(name='John Doe', age=20)
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    age
      Extra inputs are not permitted [type=extra_forbidden, input_value=20, input_type=int]
    """
```

## Populate by Name

In case you set an alias, you can still populate the model by the original name.

You need to set `populate_by_name=True` in the `model_config`:

```py
from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(alias='full_name')  # (1)!
    age: int


user = User(full_name='John Doe', age=20)  # (2)!
print(user)
#> name='John Doe' age=20
user = User(name='John Doe', age=20)  # (3)!
print(user)
#> name='John Doe' age=20
```

1. The field `'name'` has an alias `'full_name'`.
2. The model is populated by the alias `'full_name'`.
3. The model is populated by the field name `'name'`.

## Validate Assignment

The default behavior of Pydantic is to validate the data when the model is created.

In case the user changes the data after the model is created, the model is _not_ revalidated.

```py
from pydantic import BaseModel


class User(BaseModel):
    name: str


user = User(name='John Doe')  # (1)!
print(user)
#> name='John Doe'
user.name = 123  # (1)!
print(user)
#> name=123
```

1. The validation happens only when the model is created.
2. The validation does not happen when the data is changed.

In case you want to revalidate the model when the data is changed, you can use `validate_assignment=True`:

```py
from pydantic import BaseModel, ValidationError


class User(BaseModel, validate_assignment=True):  # (1)!
    name: str


user = User(name='John Doe')  # (2)!
print(user)
#> name='John Doe'
try:
    user.name = 123  # (3)!
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    name
      Input should be a valid string [type=string_type, input_value=123, input_type=int]
    """
```

1. You can either use class keyword arguments, or `model_config` to set `validate_assignment=True`.
2. The validation happens when the model is created.
3. The validation _also_ happens when the data is changed.

## Revalidate instances

By default, model and dataclass instances are not revalidated during validation.

```py upgrade="skip"
from typing import List

from pydantic import BaseModel


class User(BaseModel, revalidate_instances='never'):  # (1)!
    hobbies: List[str]


class SubUser(User):
    sins: List[str]


class Transaction(BaseModel):
    user: User


my_user = User(hobbies=['reading'])
t = Transaction(user=my_user)
print(t)
#> user=User(hobbies=['reading'])

my_user.hobbies = [1]  # (2)!
t = Transaction(user=my_user)  # (3)!
print(t)
#> user=User(hobbies=[1])

my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])
t = Transaction(user=my_sub_user)
print(t)
#> user=SubUser(hobbies=['scuba diving'], sins=['lying'])
```

1. `revalidate_instances` is set to `'never'` by **default.
2. The assignment is not validated, unless you set `validate_assignment` to `True` in the model's config.
3. Since `revalidate_instances` is set to `never`, this is not revalidated.

If you want to revalidate instances during validation, you can set `revalidate_instances` to `'always'`
in the model's config.

```py upgrade="skip"
from typing import List

from pydantic import BaseModel, ValidationError


class User(BaseModel, revalidate_instances='always'):  # (1)!
    hobbies: List[str]


class SubUser(User):
    sins: List[str]


class Transaction(BaseModel):
    user: User


my_user = User(hobbies=['reading'])
t = Transaction(user=my_user)
print(t)
#> user=User(hobbies=['reading'])

my_user.hobbies = [1]
try:
    t = Transaction(user=my_user)  # (2)!
except ValidationError as e:
    print(e)
    """
    1 validation error for Transaction
    user.hobbies.0
      Input should be a valid string [type=string_type, input_value=1, input_type=int]
    """

my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])
t = Transaction(user=my_sub_user)
print(t)  # (3)!
#> user=User(hobbies=['scuba diving'])
```

1. `revalidate_instances` is set to `'always'`.
2. The model is revalidated, since `revalidate_instances` is set to `'always'`.
3. Using `'never'` we would have gotten `user=SubUser(hobbies=['scuba diving'], sins=['lying'])`.

It's also possible to set `revalidate_instances` to `'subclass-instances'` to only revalidate instances
of subclasses of the model.

```py upgrade="skip"
from typing import List

from pydantic import BaseModel


class User(BaseModel, revalidate_instances='subclass-instances'):  # (1)!
    hobbies: List[str]


class SubUser(User):
    sins: List[str]


class Transaction(BaseModel):
    user: User


my_user = User(hobbies=['reading'])
t = Transaction(user=my_user)
print(t)
#> user=User(hobbies=['reading'])

my_user.hobbies = [1]
t = Transaction(user=my_user)  # (2)!
print(t)
#> user=User(hobbies=[1])

my_sub_user = SubUser(hobbies=['scuba diving'], sins=['lying'])
t = Transaction(user=my_sub_user)
print(t)  # (3)!
#> user=User(hobbies=['scuba diving'])
```

1. `revalidate_instances` is set to `'subclass-instances'`.
2. This is not revalidated, since `my_user` is not a subclass of `User`.
3. Using `'never'` we would have gotten `user=SubUser(hobbies=['scuba diving'], sins=['lying'])`.

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
