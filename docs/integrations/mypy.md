Pydantic works well with [mypy](http://mypy-lang.org) right out of the box.

However, Pydantic also ships with a mypy plugin that adds a number of important pydantic-specific
features to mypy that improve its ability to type-check your code.

For example, consider the following script:

```py test="skip"
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Model(BaseModel):
    age: int
    first_name = 'John'
    last_name: Optional[str] = None
    signup_ts: Optional[datetime] = None
    list_of_ints: List[int]


m = Model(age=42, list_of_ints=[1, '2', b'3'])
print(m.middle_name)  # not a model field!
Model()  # will raise a validation error for age and list_of_ints
```

Without any special configuration, mypy catches one of the errors:

```
16: error: "Model" has no attribute "middle_name"  [attr-defined]
```

But [with the plugin enabled](#enabling-the-plugin), it catches both:
```
9: error: Untyped fields disallowed  [pydantic-field]
16: error: "Model" has no attribute "middle_name"  [attr-defined]
17: error: Missing named argument "age" for "Model"  [call-arg]
17: error: Missing named argument "list_of_ints" for "Model"  [call-arg]
```

With the pydantic mypy plugin, you can fearlessly refactor your models knowing mypy will catch any mistakes
if your field names or types change.

There are other benefits too! See below for more details.

## Using mypy without the plugin

You can run your code through mypy with:

```bash
mypy \
  --ignore-missing-imports \
  --follow-imports=skip \
  --strict-optional \
  pydantic_mypy_test.py
```

### Strict Optional

For your code to pass with `--strict-optional`, you need to use `Optional[]` or an alias of `Optional[]`
for all fields with `None` as the default. (This is standard with mypy.)

### Other Pydantic interfaces

Pydantic [dataclasses](../concepts/dataclasses.md) and the [`validate_call` decorator](../concepts/validation_decorator.md)
should also work well with mypy.

## Mypy Plugin Capabilities

### Generate a signature for `Model.__init__`
* Any required fields that don't have dynamically-determined aliases will be included as required
  keyword arguments.
* If `Config.populate_by_name=True`, the generated signature will use the field names,
  rather than aliases.
* If `Config.extra='forbid'` and you don't make use of dynamically-determined aliases, the generated signature
  will not allow unexpected inputs.
* **Optional:** If the [`init_forbid_extra` **plugin setting**](#configuring-the-plugin) is set to `True`, unexpected inputs to
  `__init__` will raise errors even if `Config.extra` is not `'forbid'`.
* **Optional:** If the [`init_typed` **plugin setting**](#configuring-the-plugin) is set to `True`, the generated signature
  will use the types of the model fields (otherwise they will be annotated as `Any` to allow parsing).

### Generate a typed signature for `Model.model_construct`
* The [`model_construct`](../concepts/models.md#creating-models-without-validation) method is an alternative to `__init__`
  when input data is known to be valid and should not be parsed. Because this method performs no runtime validation,
  static checking is important to detect errors.

### Respect `Config.frozen`
* If `Config.frozen` is `True`, you'll get a mypy error if you try to change
  the value of a model field; cf. [faux immutability](../concepts/models.md#faux-immutability).

### Generate a signature for `dataclasses`
* classes decorated with [`@pydantic.dataclasses.dataclass`](../concepts/dataclasses.md) are type checked the same as standard Python dataclasses
* The `@pydantic.dataclasses.dataclass` decorator accepts a `config` keyword argument which has the same meaning as [the `Config` sub-class](../concepts/config.md).

### Respect the type of the `Field`'s `default` and `default_factory`
* Field with both a `default` and a `default_factory` will result in an error during static checking.
* The type of the `default` and `default_factory` value must be compatible with the one of the field.

### Warn about the use of untyped fields
* You'll get a mypy error any time you assign a public attribute on a model without annotating its type
* If your goal is to set a ClassVar, you should explicitly annotate the field using typing.ClassVar

## Optional Capabilities:
### Prevent the use of required dynamic aliases

* If the [`warn_required_dynamic_aliases` **plugin setting**](#configuring-the-plugin) is set to `True`, you'll get a mypy
  error any time you use a dynamically-determined alias or alias generator on a model with
  `Config.populate_by_name=False`.
* This is important because if such aliases are present, mypy cannot properly type check calls to `__init__`.
  In this case, it will default to treating all arguments as optional.

## Enabling the Plugin

To enable the plugin, just add `pydantic.mypy` to the list of plugins in your
[mypy config file](https://mypy.readthedocs.io/en/latest/config_file.html)
(this could be `mypy.ini`, `pyproject.toml`, or `setup.cfg`).

To get started, all you need to do is create a `mypy.ini` file with following contents:
```ini
[mypy]
plugins = pydantic.mypy
```

The plugin is compatible with mypy versions `>=0.930`.

See the [plugin configuration](#configuring-the-plugin) docs for more details.

### Configuring the Plugin
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
```
