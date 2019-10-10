Behaviour of pydantic can be controlled via the `Config` class on a model.

Options:

**`title`**
: the title for the generated JSON Schema

**`anystr_strip_whitespace`**
: whether to strip leading and trailing whitespace for str & byte types (default: `False`)

**`min_anystr_length`**
: the min length for str & byte types (default: `0`)

**`max_anystr_length`**
: the max length for str & byte types (default: `2 ** 16`)

**`validate_all`**
: whether to validate field defaults (default: `False`)

**`extra`**
: whether to ignore, allow, or forbid extra attributes during model initialization. Accepts the string values of
  `'ignore'`, `'allow'`, or `'forbid'`, or values of the `Extra` enum (default: `Extra.ignore`)
  
**`allow_mutation`**
: whether or not models are faux-immutable, i.e. whether `__setattr__` is allowed (default: `True`)

**`use_enum_values`**
: whether to populate models with the `value` property of enums, rather than the raw enum.
  This may be useful if you want to serialise `model.dict()` later (default: `False`)
  
**`fields`**
: a `dict` containing schema information for each field; this is equivalent to
  using [the schema](schema.md) class (default: `None`)

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
: whether to allow arbitrary user types for fields (they are validated simply by checking if the
  value is an instance of the type). If `False`, `RuntimeError` will be raised on model declaration (default: `False`)
  
**`orm_mode`**
: whether to allow usage of [ORM mode](models.md#orm-mode)

**`getter_dict`**
: a custom class (which should inherit from `GetterDict`) to use when decomposing ORM classes for validation,
  for use with `orm_mode`
  
**`alias_generator`**
: a callable that takes a field name and returns an alias for it

**`keep_untouched`**
: a tuple of types (e.g. descriptors) that should not be changed during model creation and will not be
  included in the model schemas
  
**`schema_extra`**
: a `dict` used to extend/update the generated JSON Schema

**`json_loads`**
: a custom function for decoding JSON; see [custom JSON (de)serialisation](exporting_models.md#custom-json-deserialisation)

**`json_dumps`**
: a custom function for encoding JSON; see [custom JSON (de)serialisation](exporting_models.md#custom-json-deserialisation)

**`json_encoders`**
: a `dict` used to customise the way types are encoded to JSON; see [JSON Serialisation](exporting_models.md#modeljson)

```py
{!./examples/config.py!}
```
_(This script is complete, it should run "as is")_

Similarly, if using the `@dataclass` decorator:

```py
{!./examples/ex_dataclasses_config.py!}
```
_(This script is complete, it should run "as is")_

## Alias Generator

If data source field names do not match your code style (e. g. CamelCase fields),
you can automatically generate aliases using `alias_generator`:

```py
{!./examples/alias_generator_config.py!}
```
_(This script is complete, it should run "as is")_
