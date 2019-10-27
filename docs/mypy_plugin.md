Pydantic works well with [mypy](http://mypy-lang.org/) right [out of the box](usage/mypy.md).

However, Pydantic also ships with a mypy plugin that adds a number of important pydantic-specific
features to mypy that improve its ability to type-check your code.

For example, consider the following script:
```py
{!.tmp_examples/mypy.py!}
```

Without any set up, mypy catches one of the errors:
```
13: error: "Model" has no attribute "middle_name"
```

But with the plugin enabled, it catches both:
```
13: error: "Model" has no attribute "middle_name"
16: error: Missing named argument "age" for "Model"
16: error: Missing named argument "list_of_ints" for "Model"
```

With the pydantic mypy plugin, you can fearlessly refactor your models knowing mypy will catch any mistakes
if your field names or types change.

There are other benefits too! See below for more details.

### Plugin Capabilities

#### Generate a signature for `Model.__init__`
* Any required fields that don't have dynamically-determined aliases will be included as required
  keyword arguments.
* If `Config.allow_population_by_field_name=True`, the generated signature will use the field names,
  rather than aliases.
* For subclasses of `BaseSettings`, all fields are treated as optional since they may be read from the environment.
* If `Config.extra="forbid"` and you don't make use of dynamically-determined aliases, the generated signature
  will not allow unexpected inputs.
* **Optional:** If the `init_allow_extra` **plugin setting** (see below) is set to `False`, unexpected inputs to
  `__init__` will raise errors even if `Config.extra` is not `"forbid"`.
* **Optional:** If the `init_typed` **plugin setting** (see below) is set to `True`, the generated signature
  will use the types of the model fields (otherwise they will be annotated as `Any` to allow parsing).
 
#### Generate a typed signature for `Model.construct`
* This method is a (potentially much faster) alternative to `__init__` when input data is known to be valid,
  and does not need to be  parsed 
* However, this method performs no runtime validation, so static checks are important to detect errors.

#### Respect `Config.allow_mutation`
* If `Config.allow_mutation` is `False`, you'll get a mypy error if you try to change the value of a model field.

#### Respect `Config.orm_mode`
* If `Config.orm_mode` is `False`, you'll get a mypy error if you try to call `.from_orm()`.
 
### Optional Capabilites:
#### Prevent the use of required dynamic aliases
* If the `allow_required_dynamic_aliases` **plugin setting** (see below) is set to `False`, you'll get a mypy
  error any time you use a dynamically-determined alias or alias generator on a model with
`Config.allow_population_by_field_name=False`.
* This is important because if such aliases are present, mypy cannot properly type check calls to `__init__`.
  In this case, it will default to treating all arguments as optional. 

#### Prevent the use of untyped fields
* If the `allow_untyped_fields` **plugin setting** (see below) is set to `False`, you'll get a mypy error
  any time you create a field on a model without annotating its type.
* This is important because non-annotated fields may result in **validators being applied in a surprising order**.
* In addition, mypy may not be able to correctly infer the type of the field, and may miss
  checks or raise spurious errors.

### Enabling the Plugin

To enable the plugin, just add `pydantic.mypy` to the list of plugins in your mypy config file.

For example, a `mypy.ini` file with the pydantic mypy plugin enabled might look like this:
```ini
[mypy]
plugins = pydantic.mypy

follow_imports = silent
strict_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
disallow_any_generics = True
check_untyped_defs = True

# for strict mypy: (this is the tricky one :-))
disallow_untyped_defs = True
```

### Plugin Settings

The plugin offers a few optional strictness flags if you want even stronger checks:

* `allow_required_dynamic_aliases` (default: `True`)

  If `False`, raise a mypy error whenever a model is created for which
 calls to its `__init__` or `construct` methods require the use of aliases that cannot be statically determined.
 This is the case, for example, if `allow_population_by_field_name=False` and the model uses an alias generator.

* `allow_untyped_fields` (default: `True`)

  If `False`, raise a mypy error whenever a field is declared on a model without explicitly specifying its type.

* `init_allow_extra` (default: `True`)

  If `False`, disallow extra arguments to the `__init__` call even when `Config.extra` is not `"forbid"`.
  
* `init_typed` (default: `False`)

  If `True`, include the field types as type hints in the generated signature for the `__init__` method.
  This means that you'll get mypy errors if you pass an argument that is not already the right type to
  `__init__`, even if parsing could safely convert the type.

#### Configuring the Plugin
To change the values of the plugin settings, create a section in your mypy config file called `[pydantic-mypy]`,
and add any key-value pairs for settings you want to override.

A `mypy.ini` file with all strictness flags enabled might look like this: 
```ini
[mypy]
plugins = pydantic.mypy

follow_imports = silent
strict_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
disallow_any_generics = True
check_untyped_defs = True

# for strict mypy: (this is the tricky one :-))
disallow_untyped_defs = True

[pydantic-mypy]
allow_required_dynamic_aliases = False
allow_untyped_fields = False
init_allow_extra = False
init_typed = True
```
