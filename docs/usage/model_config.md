Behaviour of _pydantic_ can be controlled via the `model_config` attribute on a `BaseModel`.

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


class Model(BaseModel, extra='forbid'):
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

Similarly, if using the `@dataclass` decorator from _pydantic_:
```py
from datetime import datetime

from pydantic import ConfigDict, ValidationError
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(str_max_length=10, validate_assignment=True))  # (1)!
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


1. If using the `dataclass` from the standard library, you should use `__pydantic_config__` instead.
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

**`title`**
: the title for the generated JSON Schema

**`str_strip_whitespace`**
: whether to strip leading and trailing whitespace for str & byte types (default: `False`)

**`str_to_upper`**
: whether to make all characters uppercase for str & byte types (default: `False`)

**`str_to_lower`**
: whether to make all characters lowercase for str & byte types (default: `False`)

**`str_min_length`**
: the min length for str & byte types (default: `0`)

**`str_max_length`**
: the max length for str & byte types (default: `None`)

**`validate_all`**
: whether to validate field defaults (default: `False`)

**`extra`**
: whether to ignore, allow, or forbid extra attributes during model initialization. Accepts the string values of
  `'ignore'`, `'allow'`, or `'forbid'`, or values of the `Extra` enum (default: `Extra.ignore`).
  `'forbid'` will cause validation to fail if extra attributes are included, `'ignore'` will silently ignore any extra attributes,
  and `'allow'` will assign the attributes to the model.

**`allow_mutation`**
: whether or not models are faux-immutable, i.e. whether `__setattr__` is allowed (default: `True`)

**`frozen`**
: setting `frozen=True` does everything that `allow_mutation=False` does, and also generates a `__hash__()` method for the model. This makes instances of the model potentially hashable if all the attributes are hashable. (default: `False`)

**`use_enum_values`**
: whether to populate models with the `value` property of enums, rather than the raw enum.
  This may be useful if you want to serialise `model.model_dump()` later (default: `False`)

**`fields`**
: a `dict` containing schema information for each field; this is equivalent to
  using [the `Field` class](schema.md), except when a field is already
  defined through annotation or the Field class, in which case only
  `alias`, `include`, `exclude`, `min_length`, `max_length`, `regex`, `gt`, `lt`, `gt`, `le`,
  `multiple_of`, `max_digits`, `decimal_places`, `min_items`, `max_items`, `unique_items`
  and `allow_mutation` can be set (for example you cannot set default of `default_factory`)
   (default: `None`)

**`validate_assignment`**
: whether to perform validation on *assignment* to attributes (default: `False`)

**`populate_by_name`**
: whether an aliased field may be populated by its name as given by the model
  attribute, as well as the alias (default: `False`)

!!! note
    The name of this configuration setting was changed in **v2.0** from
    `allow_population_by_alias` to `populate_by_name`.

**`error_msg_templates`**
: a `dict` used to override the default error message templates.
  Pass in a dictionary with keys matching the error messages you want to override (default: `{}`)

**`arbitrary_types_allowed`**
: whether to allow arbitrary user types for fields (they are validated simply by
  checking if the value is an instance of the type). If `False`, `RuntimeError` will be
  raised on model declaration (default: `False`). See an example in
  [Field Types](types/types.md#arbitrary-types-allowed).

**`from_attributes`**
: whether to allow usage of [ORM mode](models.md#orm-mode-aka-arbitrary-class-instances) (default: `False`)

!!! note
    The name of this configuration setting was changed in **v2.0** from
    `orm_mode` to `from_attributes`.

**`loc_by_alias`**
: whether to use the alias for error `loc`s (default: `True`)

**`revalidate_instances`**
: when and how to revalidate models and dataclasses during validation. Accepts the string values of
  `'never'`, `'always'` and `'subclass-instances'` (default: `'never'`).

  * `'never'` will not revalidate models and dataclasses during validation.
  * `'always'` will revalidate models and dataclasses during validation.
  * `'subclass-instances'` will revalidate models and dataclasses during validation if the instance is a subclass of the model or dataclass.

**`ser_json_timedelta`**
: the format of JSON serialized timedeltas. Accepts the string values of
  `'iso8601'` and `'float'` (default: `'iso8601'`).

  * `'iso8601'` will serialize timedeltas to ISO 8601 durations.
  * `'float'` will serialize timedeltas to the total number of seconds.

**`ser_json_bytes`**
: the encoding of JSON serialized bytes. Accepts the string values of
  `'utf8'` and `'base64'` (default: `'utf8'`).

  * `'utf8'` will serialize bytes to UTF-8 strings.
  * `'base64'` will serialize bytes to base64 strings.

**`validate_default`**
: whether to validate default values during validation (default: `False`).

**`getter_dict`**
: a custom class (which should inherit from `GetterDict`) to use when decomposing arbitrary classes
for validation, for use with `from_attributes`; see [Data binding](models.md#data-binding).

**`alias_generator`**
: a callable that takes a field name and returns an alias for it; see [the dedicated section](#alias-generator)

**`ignored_types`**
: a tuple of types that may occur as values of class attributes without annotations; this is typically used for
custom descriptors (classes that behave like `property`). If an attribute is set on a class without an annotation
and has a type that is not in this tuple (or otherwise recognized by pydantic), an error will be raised.

**`allow_inf_nan`**
: whether to allow infinity (`+inf` an `-inf`) and NaN values to float fields, defaults to `True`,
  set to `False` for compatibility with `JSON`,
  see [#3994](https://github.com/pydantic/pydantic/pull/3994) for more details, added in **V1.10**

**`protected_namespaces`**
: a `tuple` of strings that prevent model to have field which conflict with them (default: `('model_', )`).
see [the dedicated section](#protected-namespaces)

**`hide_input_in_errors`**
: whether to show input value and input type in `ValidationError` representation defaults to `False`.
see [the dedicated section](#hide-input-in-errors)

## Change behaviour globally

If you wish to change the behaviour of _pydantic_ globally, you can create your own custom `BaseModel`
with custom `model_config` since the config is inherited
```py
from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class MyClass:
    """A random class"""


class Model(BaseModel):
    x: MyClass
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

TODO: This section needs to be re-written.

!!! warning
    Alias priority logic changed in **v1.4** to resolve buggy and unexpected behaviour in previous versions.
    In some circumstances this may represent a **breaking change**,
    see [#1178](https://github.com/pydantic/pydantic/issues/1178) and the precedence order below for details.

In the case where a field's alias may be defined in multiple places,
the selected value is determined as follows (in descending order of priority):

1. Set via `Field(..., alias=<alias>)`, directly on the model
2. Defined in `Config.fields`, directly on the model
3. Set via `Field(..., alias=<alias>)`, on a parent model
4. Defined in `Config.fields`, on a parent model
5. Generated by `alias_generator`, regardless of whether it's on the model or a parent

!!! note
    This means an `alias_generator` defined on a child model **does not** take priority over an alias defined
    on a field in a parent model.

For example:

```py
from pydantic import BaseModel, Field


class Voice(BaseModel):
    name: str = Field(None, alias='ActorName')
    language_code: str = None
    mood: str = None


def alias_generator(string: str) -> str:
    # this is the same as `alias_generator = to_camel` above
    return ''.join(word.capitalize() for word in string.split('_'))


class Character(Voice):
    model_config = dict(alias_generator=alias_generator)
    act: int = 1


print(Character.model_json_schema(by_alias=True))
"""
{
    'type': 'object',
    'properties': {
        'ActorName': {'type': 'string', 'default': None, 'title': 'Actorname'},
        'LanguageCode': {'type': 'string', 'default': None, 'title': 'Languagecode'},
        'Mood': {'type': 'string', 'default': None, 'title': 'Mood'},
        'Act': {'type': 'integer', 'default': 1, 'title': 'Act'},
    },
    'title': 'Character',
}
"""
```

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

## Protected Namespaces

_Pydantic_ prevents collisions between model attributes and `BaseModel`'s own methods by
namespacing them with the prefix `model_`.
This is customizable using the `protected_namespaces` setting in the model's config so that
you can allow overriding `model_` or add your own protected namespaces.

```py
from pydantic import BaseModel

try:

    class Model(BaseModel):
        model_prefixed_field: str

except NameError as e:
    print(e)
    #> Field "model_prefixed_field" has conflict with protected namespace "model_"
```

You can change it or define multiple value for it:

```py
from pydantic import BaseModel, ConfigDict

try:

    class Model(BaseModel):
        model_prefixed_field: str
        also_protect_field: str

        model_config = ConfigDict(protected_namespaces=('protect_me_', 'also_protect_'))

except NameError as e:
    print(e)
    #> Field "also_protect_field" has conflict with protected namespace "also_protect_"
```

## Hide Input in Errors

_Pydantic_ shows the input value and type when it raises `ValidationError` during the validation.

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
