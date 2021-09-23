Behaviour of _pydantic_ can be controlled via the `Config` class on a model or a _pydantic_ dataclass.

```py
{!.tmp_examples/model_config_main.py!}
```
_(This script is complete, it should run "as is")_

Also, you can specify config options as model class kwargs:
```py
{!.tmp_examples/model_config_class_kwargs.py!}
```
_(This script is complete, it should run "as is")_

Similarly, if using the `@dataclass` decorator:
```py
{!.tmp_examples/model_config_dataclass.py!}
```
_(This script is complete, it should run "as is")_

## Options

**`title`**
: the title for the generated JSON Schema

**`anystr_strip_whitespace`**
: whether to strip leading and trailing whitespace for str & byte types (default: `False`)

**`anystr_lower`**
: whether to make all characters lowercase for str & byte types (default: `False`)

**`min_anystr_length`**
: the min length for str & byte types (default: `0`)

**`max_anystr_length`**
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
  This may be useful if you want to serialise `model.dict()` later (default: `False`)

**`fields`**
: a `dict` containing schema information for each field; this is equivalent to
  using [the `Field` class](schema.md) (default: `None`)

**`validate_assignment`**
: whether to perform validation on *assignment* to attributes (default: `False`)

**`allow_population_by_field_name`**
: whether an aliased field may be populated by its name as given by the model
  attribute, as well as the alias (default: `False`)

!!! note
    The name of this configuration setting was changed in **v1.0** from
    `allow_population_by_alias` to `allow_population_by_field_name`.

**`error_msg_templates`**
: a `dict` used to override the default error message templates.
  Pass in a dictionary with keys matching the error messages you want to override (default: `{}`)

**`arbitrary_types_allowed`**
: whether to allow arbitrary user types for fields (they are validated simply by
  checking if the value is an instance of the type). If `False`, `RuntimeError` will be
  raised on model declaration (default: `False`). See an example in
  [Field Types](types.md#arbitrary-types-allowed).

**`orm_mode`**
: whether to allow usage of [ORM mode](models.md#orm-mode-aka-arbitrary-class-instances)

**`getter_dict`**
: a custom class (which should inherit from `GetterDict`) to use when decomposing arbitrary classes
for validation, for use with `orm_mode`; see [Data binding](models.md#data-binding).

**`alias_generator`**
: a callable that takes a field name and returns an alias for it (see [the dedicated section](#alias-generator))

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
: whether to treat any underscore non-class var attrs as private, or leave them as is; See [Private model attributes](models.md#private-model-attributes)

**`copy_on_model_validation`**
: whether or not inherited models used as fields should be reconstructed (copied) on validation instead of being kept untouched (default: `True`)

## Change behaviour globally

If you wish to change the behaviour of _pydantic_ globally, you can create your own custom `BaseModel`
with custom `Config` since the config is inherited
```py
{!.tmp_examples/model_config_change_globally_custom.py!}
```
_(This script is complete, it should run "as is")_

## Alias Generator

If data source field names do not match your code style (e. g. CamelCase fields),
you can automatically generate aliases using `alias_generator`:

```py
{!.tmp_examples/model_config_alias_generator.py!}
```
_(This script is complete, it should run "as is")_

Here camel case refers to ["upper camel case"](https://en.wikipedia.org/wiki/Camel_case) aka pascal case
e.g. `CamelCase`. If you'd like instead to use lower camel case e.g. `camelCase`,
it should be trivial to modify the `to_camel` function above.

## Alias Precedence

!!! warning
    Alias priority logic changed in **v1.4** to resolve buggy and unexpected behaviour in previous versions.
    In some circumstances this may represent a **breaking change**,
    see [#1178](https://github.com/samuelcolvin/pydantic/issues/1178) and the precedence order below for details.

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
{!.tmp_examples/model_config_alias_precedence.py!}
```
_(This script is complete, it should run "as is")_
