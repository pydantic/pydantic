Behaviour of pydantic can be controlled via the `Config` class on a model.

Options:

**`title`**
: title for the generated JSON Schema

**`anystr_strip_whitespace`**
: strip or not trailing and leading whitespace for str & byte types (default: `False`)

**`min_anystr_length`**
: min length for str & byte types (default: `0`)

**`max_anystr_length`**
: max length for str & byte types (default: `2 ** 16`)

**`validate_all`**
: whether or not to validate field defaults (default: `False`)

**`extra`**
: whether to ignore, allow or forbid extra attributes in model. Can use either string values of `ignore`,
  `allow` or `forbid`, or use `Extra` enum (default is `Extra.ignore`)
  
**`allow_mutation`**
: whether or not models are faux-immutable, e.g. __setattr__ fails (default: `True`)

**`use_enum_values`**
: whether to populate models with the `value` property of enums,
  rather than the raw enum - useful if you want to serialise `model.dict()` later (default: `False`)
  
**`fields`**
: schema information on each field, this is equivilant to
  using [the schema](schema.md) class (default: `None`)
  
**`validate_assignment`**
: whether to perform validation on assignment to attributes or not (default: `False`)

**`allow_population_by_field_name`**
: whether or not an aliased field may be populated by its name as given by the model
  attribute, as well as the alias (default: `False`)

!!! note
    The name of this configuration setting was changed in **v1.0** from 
    `allow_population_by_alias` to `allow_population_by_field_name`.
  
**`error_msg_templates`**
: let's you to override default error message templates.
  Pass in a dictionary with keys matching the error messages you want to override (default: `{}`)
  
**`arbitrary_types_allowed`**
: whether to allow arbitrary user types for fields (they are validated simply by checking if the
  value is instance of that type). If `False` - `RuntimeError` will be raised on model declaration (default: `False`)
  
**`orm_mode`**
: allows usage of [ORM mode](models.md#orm-mode)

**`getter_dict`**
: custom class (should inherit from `GetterDict`) to use when decomposing ORM classes for validation,
  use with `orm_mode`
  
**`alias_generator`**
: callable that takes field name and returns alias for it

**`keep_untouched`**
: tuple of types (e. g. descriptors) that won't change during model creation and won't be
  included in the model schemas
  
**`schema_extra`**
: takes a `dict` to extend/update the generated JSON Schema

**`json_loads`**
: custom function for decoding JSON, see [custom JSON (de)serialisation](exporting_models.md#custom-json-deserialisation)

**`json_dumps`**
: custom function for encoding JSON, see [custom JSON (de)serialisation](exporting_models.md#custom-json-deserialisation)

**`json_encoders`**
: customise the way types are encoded to JSON, see [JSON Serialisation](exporting_models.md#modeljson)

```py
{!./examples/config.py!}
```
_(This script is complete, it should run "as is")_

Version for models based on `@dataclass` decorator:

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
