Pydantic works well with [mypy](http://mypy-lang.org/) right [out of the box](usage/mypy.md).

However, Pydantic also ships with a mypy plugin that adds a number of important pydantic-specific
features to mypy that improve its ability to type-check your code.

For example, consider the following script:
```py
{!.tmp_examples/mypy_main.py!}
```

Without any special configuration, mypy catches one of the errors (see [here](usage/mypy.md) for usage instructions):
```
13: error: "Model" has no attribute "middle_name"
```

But [with the plugin enabled](#enabling-the-plugin), it catches both:
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
* For subclasses of [`BaseSettings`](usage/settings.md), all fields are treated as optional since they may be
  read from the environment.
* If `Config.extra="forbid"` and you don't make use of dynamically-determined aliases, the generated signature
  will not allow unexpected inputs.
* **Optional:** If the [`init_forbid_extra` **plugin setting**](#plugin-settings) is set to `True`, unexpected inputs to
  `__init__` will raise errors even if `Config.extra` is not `"forbid"`.
* **Optional:** If the [`init_typed` **plugin setting**](#plugin-settings) is set to `True`, the generated signature
  will use the types of the model fields (otherwise they will be annotated as `Any` to allow parsing).

#### Generate a typed signature for `Model.construct`
* The [`construct`](usage/models.md#creating-models-without-validation) method is a faster alternative to `__init__`
  when input data is known to be valid and does not need to be parsed. But because this method performs no runtime
  validation, static checking is important to detect errors.

#### Respect `Config.allow_mutation`
* If `Config.allow_mutation` is `False`, you'll get a mypy error if you try to change
  the value of a model field; cf. [faux immutability](usage/models.md#faux-immutability).

#### Respect `Config.orm_mode`
* If `Config.orm_mode` is `False`, you'll get a mypy error if you try to call `.from_orm()`;
  cf. [ORM mode](usage/models.md#orm-mode-aka-arbitrary-class-instances)

#### Generate a signature for `dataclasses`
* classes decorated with [`@pydantic.dataclasses.dataclass`](usage/dataclasses.md) are type checked the same as standard Python dataclasses
* The `@pydantic.dataclasses.dataclass` decorator accepts a `config` keyword argument which has the same meaning as [the `Config` sub-class](usage/model_config.md).

#### Respect the type of the `Field`'s `default` and `default_factory`
* Field with both a `default` and a `default_factory` will result in an error during static checking.
* The type of the `default` and `default_factory` value must be compatible with the one of the field.

### Optional Capabilities:
#### Prevent the use of required dynamic aliases
* If the [`warn_required_dynamic_aliases` **plugin setting**](#plugin-settings) is set to `True`, you'll get a mypy
  error any time you use a dynamically-determined alias or alias generator on a model with
  `Config.allow_population_by_field_name=False`.
* This is important because if such aliases are present, mypy cannot properly type check calls to `__init__`.
  In this case, it will default to treating all arguments as optional.

#### Prevent the use of untyped fields
* If the [`warn_untyped_fields` **plugin setting**](#plugin-settings) is set to `True`, you'll get a mypy error
  any time you create a field on a model without annotating its type.
* This is important because non-annotated fields may result in
  [**validators being applied in a surprising order**](usage/models.md#field-ordering).
* In addition, mypy may not be able to correctly infer the type of the field, and may miss
  checks or raise spurious errors.

### Enabling the Plugin

To enable the plugin, just add `pydantic.mypy` to the list of plugins in your
[mypy config file](https://mypy.readthedocs.io/en/latest/config_file.html)
(this could be `mypy.ini` or `setup.cfg`).

To get started, all you need to do is create a `mypy.ini` file with following contents:
```ini
[mypy]
plugins = pydantic.mypy
```

The plugin is compatible with mypy versions 0.910, 0.920, 0.921 and 0.930.

See the [mypy usage](usage/mypy.md) and [plugin configuration](#configuring-the-plugin) docs for more details.

### Plugin Settings

The plugin offers a few optional strictness flags if you want even stronger checks:

* `init_forbid_extra`

    If enabled, disallow extra arguments to the `__init__` call even when `Config.extra` is not `"forbid"`.

* `init_typed`

    If enabled, include the field types as type hints in the generated signature for the `__init__` method.
    This means that you'll get mypy errors if you pass an argument that is not already the right type to
    `__init__`, even if parsing could safely convert the type.

* `warn_required_dynamic_aliases`

    If enabled, raise a mypy error whenever a model is created for which
    calls to its `__init__` or `construct` methods require the use of aliases that cannot be statically determined.
    This is the case, for example, if `allow_population_by_field_name=False` and the model uses an alias generator.

* `warn_untyped_fields`

    If enabled, raise a mypy error whenever a field is declared on a model without explicitly specifying its type.


#### Configuring the Plugin
To change the values of the plugin settings, create a section in your mypy config file called `[pydantic-mypy]`,
and add any key-value pairs for settings you want to override.

A `mypy.ini` file with all plugin strictness flags enabled (and some other mypy strictness flags, too) might look like:
```ini
[mypy]
plugins = pydantic.mypy

follow_imports = silent
warn_redundant_casts = True
warn_unused_ignores = True
disallow_any_generics = True
check_untyped_defs = True
no_implicit_reexport = True

# for strict mypy: (this is the tricky one :-))
disallow_untyped_defs = True

[pydantic-mypy]
init_forbid_extra = True
init_typed = True
warn_required_dynamic_aliases = True
warn_untyped_fields = True
```

As of `mypy>=0.900`, mypy config may also be included in the `pyproject.toml` file rather than `mypy.ini`.
The same configuration as above would be:
```toml
[tool.mypy]
plugins = [
  "pydantic.mypy"
]

follow_imports = "silent"
warn_redundant_casts = true
warn_unused_ignores = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_reexport = true

# for strict mypy: (this is the tricky one :-))
disallow_untyped_defs = true

[tool.pydantic-mypy]
init_forbid_extra = true
init_typed = true
warn_required_dynamic_aliases = true
warn_untyped_fields = true
```
