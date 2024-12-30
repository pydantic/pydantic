Pydantic works well with [mypy](http://mypy-lang.org) right out of the box.

However, Pydantic also ships with a mypy plugin that adds a number of important Pydantic-specific
features that improve its ability to type-check your code.

For example, consider the following script:

```python {test="skip" linenums="1"}
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

Without any special configuration, mypy does not catch the [missing model field annotation](../errors/usage_errors.md#model-field-missing-annotation)
and errors about the `list_of_ints` argument which Pydantic parses correctly:

```
15: error: List item 1 has incompatible type "str"; expected "int"  [list-item]
15: error: List item 2 has incompatible type "bytes"; expected "int"  [list-item]
16: error: "Model" has no attribute "middle_name"  [attr-defined]
17: error: Missing named argument "age" for "Model"  [call-arg]
17: error: Missing named argument "list_of_ints" for "Model"  [call-arg]
```

But [with the plugin enabled](#enabling-the-plugin), it gives the correct errors:
```
9: error: Untyped fields disallowed  [pydantic-field]
16: error: "Model" has no attribute "middle_name"  [attr-defined]
17: error: Missing named argument "age" for "Model"  [call-arg]
17: error: Missing named argument "list_of_ints" for "Model"  [call-arg]
```

With the pydantic mypy plugin, you can fearlessly refactor your models knowing mypy will catch any mistakes
if your field names or types change.

Note that mypy already supports some features without using the Pydantic plugin, such as synthesizing a `__init__`
method for Pydantic models and dataclasses. See the [mypy plugin capabilities](#mypy-plugin-capabilities) for a list
of additional features.

## Enabling the Plugin

To enable the plugin, just add `pydantic.mypy` to the list of plugins in your
[mypy config file](https://mypy.readthedocs.io/en/latest/config_file.html):

=== "`mypy.ini`"

    ```ini
    [mypy]
    plugins = pydantic.mypy
    ```

=== "`pyproject.toml`"

    ```toml
    [tool.mypy]
    plugins = ['pydantic.mypy']
    ```

!!! note

    If you're using `pydantic.v1` models, you'll need to add `pydantic.v1.mypy` to your list of plugins.

See the [plugin configuration](#configuring-the-plugin) for more details.

## Supported mypy versions

Pydantic supports the mypy versions released less than 6 months ago. Older versions may still work with the plugin
but won't be tested. The list of released mypy versions can be found [here](https://mypy-lang.org/news.html). Note
that the version support policy is subject to change at discretion of contributors.

## Mypy plugin capabilities

### Generate a `__init__` signature for Pydantic models

* Any required fields that don't have dynamically-determined aliases will be included as required
  keyword arguments.
* If the [`populate_by_name`][pydantic.ConfigDict.populate_by_name] model configuration value is set to
  `True`, the generated signature will use the field names rather than aliases.
* The [`init_forbid_extra`](#init_forbid_extra) and [`init_typed`](#init_typed) plugin configuration
  values can further fine-tune the synthesized `__init__` method.

### Generate a typed signature for `model_construct`

* The [`model_construct`][pydantic.BaseModel.model_construct] method is an alternative to model validation when input data is
  known to be valid and should not be parsed (see the [documentation](../concepts/models.md#creating-models-without-validation)).
  Because this method performs no runtime validation, static checking is important to detect errors.

### Support for frozen models

* If the [`frozen`][pydantic.ConfigDict.frozen] configuration is set to `True`, you will get
  an error if you try mutating a model field (see [faux immutability](../concepts/models.md#faux-immutability))

### Respect the type of the `Field`'s `default` and `default_factory`

* Field with both a `default` and a `default_factory` will result in an error during static checking.
* The type of the `default` and `default_factory` value must be compatible with the one of the field.

### Warn about the use of untyped fields

* While defining a field without an annotation will result in a [runtime error](../errors/usage_errors.md#model-field-missing-annotation),
  the plugin will also emit a type checking error.

### Prevent the use of required dynamic aliases

See the documentation of the [`warn_required_dynamic_aliases`](#warn_required_dynamic_aliases) plugin configuration value.

## Configuring the Plugin

To change the values of the plugin settings, create a section in your mypy config file called `[pydantic-mypy]`,
and add any key-value pairs for settings you want to override.

A configuration file with all plugin strictness flags enabled (and some other mypy strictness flags, too) might look like:

=== "`mypy.ini`"

    ```ini
    [mypy]
    plugins = pydantic.mypy

    follow_imports = silent
    warn_redundant_casts = True
    warn_unused_ignores = True
    disallow_any_generics = True
    no_implicit_reexport = True
    disallow_untyped_defs = True

    [pydantic-mypy]
    init_forbid_extra = True
    init_typed = True
    warn_required_dynamic_aliases = True
    ```

=== "`pyproject.toml`"

    ```toml
    [tool.mypy]
    plugins = ["pydantic.mypy"]

    follow_imports = "silent"
    warn_redundant_casts = true
    warn_unused_ignores = true
    disallow_any_generics = true
    no_implicit_reexport = true
    disallow_untyped_defs = true

    [tool.pydantic-mypy]
    init_forbid_extra = true
    init_typed = true
    warn_required_dynamic_aliases = true
    ```

### `init_typed`

Because Pydantic performs [data conversion](../concepts/models.md#data-conversion) by default, the following is still valid at runtime:

```python {test="skip" lint="skip"}
class Model(BaseModel):
    a: int


Model(a='1')
```

For this reason, the plugin will use [`Any`][typing.Any] for field annotations when synthesizing the `__init__` method,
unless `init_typed` is set or [strict mode](../concepts/strict_mode.md) is enabled on the model.

### `init_forbid_extra`

By default, Pydantic allows (and ignores) any extra provided argument:

```python {test="skip" lint="skip"}
class Model(BaseModel):
    a: int = 1


Model(unrelated=2)
```

For this reason, the plugin will add an extra `**kwargs: Any` parameter when synthesizing the `__init__` method, unless
`init_forbid_extra` is set or the [`extra`][pydantic.ConfigDict.extra] is set to `'forbid'`.

### `warn_required_dynamic_aliases`

Whether to error when using a dynamically-determined alias or alias generator on a model with
[`populate_by_name`][pydantic.ConfigDict.populate_by_name] set to `False`. If such aliases are
present, mypy cannot properly type check calls to `__init__`. In this case, it will default to
treating all arguments as not required.

!!! note "Compatibility with `Any` being disallowed"
    Some mypy configuration options (such as [`disallow_any_explicit`](https://mypy.readthedocs.io/en/stable/config_file.html#confval-disallow_any_explicit))
    will error because the synthesized `__init__` method contains [`Any`][typing.Any] annotations. To circumvent the issue, you will have
    to enable both `init_forbid_extra` and `init_typed`.
