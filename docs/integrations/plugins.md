Pydantic allows users to create plugins that can be used to extend the functionality of the library.

Plugins are installed via Python entry points. You can read more about entry points in the
[Entry points specification](https://packaging.python.org/specifications/entry-points/) from the
Python Packaging Authority.

In case you have a project called `pydantic-plugin`, you can create a plugin by adding the following
to your `pyproject.toml`:

```toml
[project.entry-points.pydantic]
pydantic_plugin = "pydantic_plugin:plugin"
```

The entry point group is `pydantic`, and the name of the entry point is the name of the plugin.

Plugins are loaded in the order they are found, and the order they are found is not guaranteed.

Using Pydantic itself in a plugin could cause an `ImportError`. To avoid such an error Pydantic allows to defer plugin
importing. To enable deferred plugin import add `defer_import` extra argument to plugin configuration in `pyproject.toml`:

```toml
[project.entry-points.pydantic]
pydantic_plugin = "pydantic_plugin:plugin [defer_import]"
```

As a user, you can modify the behavior of the plugin in a `BaseModel` using the `plugin_settings`
class keyword argument. This argument takes a dictionary of settings that will be passed to all plugins as is.
The plugin can then use these settings to modify its behavior. It is recommended for plugins to separate their settings
into their own dedicates keys in a plugin specific key in the `plugin_settings` dictionary.

```py test="skip"
from pydantic import BaseModel


class Foo(BaseModel, plugin_settings={'my-plugin': {'observe': 'all'}}):
    ...
```

## Build a plugin

??? api "API Documentation"
    [`pydantic.plugin.plugin`][pydantic.plugin.plugin]<br>

Pydantic has an API for creating plugins. The API is exposed via the `pydantic.plugin` module.

On your plugin you can _wrap_ the following methods:

* [`validate_python`][pydantic_core.SchemaValidator.validate_python]: Used to validate the data from a Python object.
* [`validate_json`][pydantic_core.SchemaValidator.validate_json]: Used to validate the data from a JSON string.

For each method, you can implement the following callbacks:

* `enter`: Called before the validation of a field starts.
* `on_success`: Called when the validation of a field succeeds.
* `on_error`: Called when the validation of a field fails.

Let's see an example of a plugin that _wraps_ the `validate_python` method of the [`SchemaValidator`][pydantic_core.SchemaValidator].

```py
from pprint import pprint
from typing import Any, Dict, Optional

from pydantic_core import ValidationError

from pydantic.plugin import OnValidatePython as _OnValidatePython
from pydantic.plugin import Plugin


class OnValidatePython(_OnValidatePython):
    def enter(
        self,
        input: Any,
        *,
        strict: Optional[bool] = None,
        from_attributes: Optional[bool] = None,
        context: Optional[Dict[str, Any]] = None,
        self_instance: Optional[Any] = None,
    ) -> None:
        pprint(input)

    def on_success(self, result: Any) -> None:
        pprint(result)

    def on_error(self, error: ValidationError) -> None:
        pprint(error.json())


plugin = Plugin(on_validate_python=OnValidatePython)
```
