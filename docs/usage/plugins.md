!!! warning "Experimental feature"
    Plugins support is experimental and is subject to change in minor releases.
    Developing plugins is not recommended until the feature becomes stable.

Pydantic allows users to create plugins that can be used to extend the functionality of the library.

Plugins are installed via Python entry points. You can read more about entry points in the
[Entry points specification](https://packaging.python.org/specifications/entry-points/) from the
Python Packaging Authority.

In case you have a project called `my-pydantic-plugin`, you can create a plugin by adding the following
to your `pyproject.toml`:

```toml
[project.entry-points.pydantic]
my_plugin = "my_pydantic_plugin:plugin"
```

The entry point group is `pydantic`, `my_plugin` is the name of the plugin, `my_pydantic_plugin` is the module to load plugin object from, and `plugin` is the object name to load.

Plugins are loaded in the order they are found, and the order they are found is not guaranteed.

As a user, you can modify the behavior of the plugin in a `BaseModel` using the `plugin_settings` [Model Config](../usage/model_config.md) argument or
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
from dataclasses import dataclass
from pprint import pprint
from typing import Any, Dict, Optional, Type

from pydantic_core import ValidationError

from pydantic.plugin import (
    ValidateJsonHandlerProtocol,
    ValidatePythonHandlerProtocol,
    PydanticPlugin,
)


class OnValidatePython(ValidatePythonHandlerProtocol):
    def on_enter(
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


@dataclass
class Plugin(PydanticPlugin):
    on_validate_python: Optional[Type[ValidatePythonHandlerProtocol]] = None
    on_validate_json: Optional[Type[ValidateJsonHandlerProtocol]] = None


plugin = Plugin(on_validate_python=OnValidatePython)
```

## Using Plugin Settings

Consider that you have a plugin called setting called "observer", then you can use it like this:

```py
from pydantic import BaseModel


class Foo(BaseModel, plugin_settings={'observer': 'all'}):
    ...
```

On each validation call, the `plugin_settings` will be passed to a callable registered for the events.
