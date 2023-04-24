Behaviour of _pydantic_ can be controlled via the `Config` class on a model or a _pydantic_ dataclass.

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

Similarly, if using the `@dataclass` decorator:
```py
from datetime import datetime

from pydantic import ValidationError
from pydantic.dataclasses import dataclass


@dataclass(config=dict(str_max_length=10, validate_assignment=True))
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

!!! warning
    This parameter is in beta

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
    The name of this configuration setting was changed in **v1.0** from
    `allow_population_by_alias` to `populate_by_name`.

**`error_msg_templates`**
: a `dict` used to override the default error message templates.
  Pass in a dictionary with keys matching the error messages you want to override (default: `{}`)

**`arbitrary_types_allowed`**
: whether to allow arbitrary user types for fields (they are validated simply by
  checking if the value is an instance of the type). If `False`, `RuntimeError` will be
  raised on model declaration (default: `False`). See an example in
  [Field Types](types/types.md#arbitrary-types-allowed).

**`undefined_types_warning`**
: whether to raise a warning if a type is undefined when a model is declared. This occurs when a type is defined in another model declared elsewhere in code which has not yet executed.
  If `True`, `UserWarning` will be raised on model declaration (default: `True`).
  See an example in [Field Types](types/types.md#undefined_types_warning).

**`from_attributes`**
: whether to allow usage of [ORM mode](models.md#orm-mode-aka-arbitrary-class-instances)

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

## Change behaviour globally

If you wish to change the behaviour of _pydantic_ globally, you can create your own custom `BaseModel`
with custom `Config` since the config is inherited
```py
from pydantic import BaseModel as PydanticBaseModel


class BaseModel(PydanticBaseModel):
    model_config = dict(arbitrary_types_allowed=True)


class MyClass:
    """A random class"""


class Model(BaseModel):
    x: MyClass
```

## Alias Generator

If data source field names do not match your code style (e. g. CamelCase fields),
you can automatically generate aliases using `alias_generator`:

```py
from pydantic import BaseModel


def to_camel(string: str) -> str:
    return ''.join(word.capitalize() for word in string.split('_'))


class Voice(BaseModel):
    model_config = dict(alias_generator=to_camel)
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
    'title': 'Character',
    'type': 'object',
    'properties': {
        'ActorName': {'type': 'string', 'default': None, 'title': 'Actorname'},
        'LanguageCode': {'type': 'string', 'default': None, 'title': 'Languagecode'},
        'Mood': {'type': 'string', 'default': None, 'title': 'Mood'},
        'Act': {'type': 'integer', 'default': 1, 'title': 'Act'},
    },
}
"""
```

## Smart Union

**TODO: Smart Union behaviour has roughly become the default, this needs to be moved to the stuff on unions**

By default, as explained [here](types/types.md#unions), _pydantic_ tries to validate (and coerce if it can) in the order of the `Union`.
So sometimes you may have unexpected coerced data.

```py
from typing import Union

from pydantic import BaseModel


class Foo(BaseModel):
    pass


class Bar(BaseModel):
    pass


class Model(BaseModel):
    x: Union[str, int]
    y: Union[Foo, Bar]


print(Model(x=1, y=Bar()))
#> x=1 y=Bar()
```

To prevent this, you can enable `Config.smart_union`. _Pydantic_ will then check all allowed types before even trying to coerce.
Know that this is of course slower, especially if your `Union` is quite big.

```py
from typing import Union

from pydantic import BaseModel


class Foo(BaseModel):
    pass


class Bar(BaseModel):
    pass


class Model(BaseModel):
    x: Union[str, int]
    y: Union[Foo, Bar]


print(Model(x=1, y=Bar()))
#> x=1 y=Bar()
```

!!! warning
    Note that this option **does not support compound types yet** (e.g. differentiate `List[int]` and `List[str]`).
    This option will be improved further once a strict mode is added in _pydantic_ and will probably be the default behaviour in v2!

```py
from typing import List, Union

from pydantic import BaseModel


class Model(BaseModel):
    x: Union[List[str], List[int]]


# Expected coercion
print(Model(x=[1, '2']))
#> x=[1, 2]

# Unexpected coercion
print(Model(x=[1, 2]))
#> x=[1, 2]
```
