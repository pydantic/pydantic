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

### Arbitrary Types Allowed

You can allow arbitrary types using the `arbitrary_types_allowed` setting in the model's config:

```py
from pydantic import BaseModel, ConfigDict, ValidationError


# This is not a pydantic model, it's an arbitrary class
class Pet:
    def __init__(self, name: str):
        self.name = name


class Model(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    pet: Pet
    owner: str


pet = Pet(name='Hedwig')
# A simple check of instance type is used to validate the data
model = Model(owner='Harry', pet=pet)
print(model)
#> pet=<__main__.Pet object at 0x0123456789ab> owner='Harry'
print(model.pet)
#> <__main__.Pet object at 0x0123456789ab>
print(model.pet.name)
#> Hedwig
print(type(model.pet))
#> <class '__main__.Pet'>
try:
    # If the value is not an instance of the type, it's invalid
    Model(owner='Harry', pet='Hedwig')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    pet
      Input should be an instance of Pet [type=is_instance_of, input_value='Hedwig', input_type=str]
    """
# Nothing in the instance of the arbitrary type is checked
# Here name probably should have been a str, but it's not validated
pet2 = Pet(name=42)
model2 = Model(owner='Harry', pet=pet2)
print(model2)
#> pet=<__main__.Pet object at 0x0123456789ab> owner='Harry'
print(model2.pet)
#> <__main__.Pet object at 0x0123456789ab>
print(model2.pet.name)
#> 42
print(type(model2.pet))
#> <class '__main__.Pet'>
```

## Protected Namespaces

Pydantic prevents collisions between model attributes and `BaseModel`'s own methods by
namespacing them with the prefix `model_`.

```py
import warnings

from pydantic import BaseModel

warnings.filterwarnings('error')  # Raise warnings as errors

try:

    class Model(BaseModel):
        model_prefixed_field: str

except UserWarning as e:
    print(e)
    """
    Field "model_prefixed_field" has conflict with protected namespace "model_".

    You may be able to resolve this warning by setting `model_config['protected_namespaces'] = ()`.
    """
```

You can customize this behavior using the `protected_namespaces` setting:

```py
import warnings

from pydantic import BaseModel, ConfigDict

warnings.filterwarnings('error')  # Raise warnings as errors

try:

    class Model(BaseModel):
        model_prefixed_field: str
        also_protect_field: str

        model_config = ConfigDict(
            protected_namespaces=('protect_me_', 'also_protect_')
        )

except UserWarning as e:
    print(e)
    """
    Field "also_protect_field" has conflict with protected namespace "also_protect_".

    You may be able to resolve this warning by setting `model_config['protected_namespaces'] = ('protect_me_',)`.
    """
```

While Pydantic will only emit a warning when an item is in a protected namespace but does not actually have a collision,
an error _is_ raised if there is an actual collision with an existing attribute:

```py
from pydantic import BaseModel

try:

    class Model(BaseModel):
        model_validate: str

except NameError as e:
    print(e)
    """
    Field "model_validate" conflicts with member <bound method BaseModel.model_validate of <class 'pydantic.main.BaseModel'>> of protected namespace "model_".
    """
```

## Hide Input in Errors

Pydantic shows the input value and type when it raises `ValidationError` during the validation.

```py
from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    a: str


try:
    Model(a=123)
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    a
      Input should be a valid string [type=string_type, input_value=123, input_type=int]
    """
```

You can hide the input value and type by setting the `hide_input_in_errors` config to `True`.

```py
from pydantic import BaseModel, ConfigDict, ValidationError


class Model(BaseModel):
    a: str

    model_config = ConfigDict(hide_input_in_errors=True)


try:
    Model(a=123)
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    a
      Input should be a valid string [type=string_type]
    """
```

## JSON schema customization

#### `json_schema_serialization_defaults_required`

By default, the JSON schema generated for serialization will mark fields as **not-required**, even if they
have a default value that would always be included during serialization. This has the benefit that most
typical types will have the same JSON schema for both validation and serialization, but has the downside
that you can often guarantee that fields will be present when dumping a model even if they don't need to
be included when initializing, and the JSON schema doesn't reflect that.

If you want to opt into having the serialization schema mark fields as required even if they have a default value,
you can set the config setting to `json_schema_serialization_defaults_required=True`:

```py
from pydantic import BaseModel, ConfigDict


class Model(BaseModel):
    a: str = 'a'

    model_config = ConfigDict(json_schema_serialization_defaults_required=True)


print(Model.model_json_schema(mode='validation'))
"""
{
    'properties': {'a': {'default': 'a', 'title': 'A', 'type': 'string'}},
    'title': 'Model',
    'type': 'object',
}
"""
print(Model.model_json_schema(mode='serialization'))
"""
{
    'properties': {'a': {'default': 'a', 'title': 'A', 'type': 'string'}},
    'required': ['a'],
    'title': 'Model',
    'type': 'object',
}
"""
```

#### `json_schema_mode_override`

If you want to be able to force a model to always use a specific mode when generating a JSON schema (even if the
mode is explicitly specified as a different value in the JSON schema generation calls), this can be done by setting
the config setting `json_schema_mode_override='serialization'` or `json_schema_mode_override='validation'`:

```py
from pydantic import BaseModel, ConfigDict, Json


class Model(BaseModel):
    a: Json[int]  # requires a string to validate, but will dump an int


print(Model.model_json_schema(mode='serialization'))
"""
{
    'properties': {'a': {'title': 'A', 'type': 'integer'}},
    'required': ['a'],
    'title': 'Model',
    'type': 'object',
}
"""


class ForceInputModel(Model):
    # the following ensures that even with mode='serialization', we
    # will get the schema that would be generated for validation.
    model_config = ConfigDict(json_schema_mode_override='validation')


print(ForceInputModel.model_json_schema(mode='serialization'))
"""
{
    'properties': {
        'a': {
            'contentMediaType': 'application/json',
            'contentSchema': {'type': 'integer'},
            'title': 'A',
            'type': 'string',
        }
    },
    'required': ['a'],
    'title': 'ForceInputModel',
    'type': 'object',
}
"""
```

This can be useful when using frameworks (such as FastAPI) that may generate different schemas for validation
and serialization that must both be referenced from the same schema; when this happens, we automatically append
`-Input` to the definition reference for the validation schema and `-Output` to the definition reference for the
serialization schema. By specifying a `json_schema_mode_override` though, this prevents the conflict between
the validation and serialization schemas (since both will use the specified schema), and so prevents the suffixes
from being added to the definition references.
