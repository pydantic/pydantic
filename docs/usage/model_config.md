Behaviour of _pydantic_ can be controlled via the `Config` class on a model or a _pydantic_ dataclass.

```py
from pydantic import ConfigDict, BaseModel, ValidationError


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
from pydantic import BaseModel, ValidationError, Extra


class Model(BaseModel, extra=Extra.forbid):
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


class MyConfig:
    str_max_length = 10
    validate_assignment = True


@dataclass(config=MyConfig)
class User:
    id: int
    name: str = 'John Doe'
    signup_ts: datetime = None


user = User(id='42', signup_ts='2032-06-21T12:00')
try:
    user.name = 'x' * 20
except ValidationError as e:
    print(e)
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
  [Field Types](types.md#arbitrary-types-allowed).

**`undefined_types_warning`**
: whether to raise a warning if a type is undefined when a model is declared. This occurs when a type is defined in another model declared elsewhere in code which has not yet executed.
  If `True`, `UserWarning` will be raised on model declaration (default: `True`).
  See an example in [Field Types](types.md#undefined_types_warning).

**`from_attributes`**
: whether to allow usage of [ORM mode](models.md#orm-mode-aka-arbitrary-class-instances)

**`getter_dict`**
: a custom class (which should inherit from `GetterDict`) to use when decomposing arbitrary classes
for validation, for use with `from_attributes`; see [Data binding](models.md#data-binding).

**`alias_generator`**
: a callable that takes a field name and returns an alias for it; see [the dedicated section](#alias-generator)

**`keep_untouched`**
: a tuple of types (e.g. descriptors) for a model's default values that should not be changed during model creation and will
not be included in the model schemas. **Note**: this means that attributes on the model with *defaults of this type*, not *annotations of this type*, will be left alone.

**`schema_extra`**
: a `dict` used to extend/update the generated JSON Schema, or a callable to post-process it; see [schema customization](schema.md#schema-customization)

**`json_loads`**
: a custom function for decoding JSON; see [custom JSON (de)serialisation](exporting_models.md#custom-json-deserialisation)

**`json_dumps`**
: a custom function for encoding JSON; see [custom JSON (de)serialisation](exporting_models.md#custom-json-deserialisation)

**`json_encoders`**
: a `dict` used to customise the way types are encoded to JSON; see [JSON Serialisation](exporting_models.md#modeljson)

**`underscore_attrs_are_private`**
: whether to treat any underscore non-class var attrs as private, or leave them as is; see [Private model attributes](models.md#private-model-attributes)

**`copy_on_model_validation`**
: string literal to control how models instances are processed during validation,
with the following means (see [#4093](https://github.com/pydantic/pydantic/pull/4093) for a full discussion of the changes to this field):

* `'none'` - models are not copied on validation, they're simply kept "untouched"
* `'shallow'` - models are shallow copied, this is the default
* `'deep'` - models are deep copied

**`smart_union`**
: whether _pydantic_ should try to check all types inside `Union` to prevent undesired coercion; see [the dedicated section](#smart-union)

**`post_init_call`**
: whether stdlib dataclasses `__post_init__` should be run before (default behaviour with value `'before_validation'`)
  or after (value `'after_validation'`) parsing and validation when they are [converted](dataclasses.md#stdlib-dataclasses-and-_pydantic_-dataclasses).

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
    class Config:
        arbitrary_types_allowed = True


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
    name: str
    language_code: str

    class Config:
        alias_generator = to_camel


voice = Voice(Name='Filiz', LanguageCode='tr-TR')
print(voice.language_code)
print(voice.model_dump(by_alias=True))
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


class Character(Voice):
    act: int = 1

    class Config:
        fields = {'language_code': 'lang'}

        @classmethod
        def alias_generator(cls, string: str) -> str:
            # this is the same as `alias_generator = to_camel` above
            return ''.join(word.capitalize() for word in string.split('_'))


print(Character.model_json_schema(by_alias=True))
```

## Smart Union

By default, as explained [here](types.md#unions), _pydantic_ tries to validate (and coerce if it can) in the order of the `Union`.
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

    class Config:
        smart_union = True


print(Model(x=1, y=Bar()))
```

!!! warning
    Note that this option **does not support compound types yet** (e.g. differentiate `List[int]` and `List[str]`).
    This option will be improved further once a strict mode is added in _pydantic_ and will probably be the default behaviour in v2!

```py
from typing import List, Union

from pydantic import BaseModel


class Model(BaseModel, smart_union=True):
    x: Union[List[str], List[int]]


# Expected coercion
print(Model(x=[1, '2']))

# Unexpected coercion
print(Model(x=[1, 2]))
```
