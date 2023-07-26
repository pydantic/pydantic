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

As a user, you can modify the behavior of the plugin in a `BaseModel` using the `plugin_settings`
class keyword argument. This argument takes a dictionary of settings that will be passed to the
plugin. The plugin can then use these settings to modify its behavior.

```py test="skip"
from pydantic import BaseModel


class Foo(BaseModel, plugin_settings=dict(observe='all')):
    ...
```

## Build a plugin

??? api "API Documentation"
    [`pydantic.plugin.plugin`][pydantic.plugin.plugin]<br>

??? api "API Documentation"
    [`pydantic.plugin`][pydantic.plugin]<br>

Pydantic has an API for creating plugins. The API is exposed via the `pydantic.plugin` module.

On your plugin you can _wrap_ the following methods:

* [`validate_python`][validate python]: Used to validate the data from a Python object.
* [`validate_json`][validate json]: Used to validate the data from a JSON string.

For each method, you can implement the following callbacks:

* `enter`: Called before the validation of a field starts.
* `on_success`: Called when the validation of a field succeeds.
* `on_error`: Called when the validation of a field fails.

Let's see an example of a plugin that _wraps_ the `validate_python` method of the [`SchemaValidator`][schema validator].

```py
from pprint import pprint
from typing import Any

from pydantic_core import ValidationError

from pydantic.plugin import OnValidatePython as _OnValidatePython
from pydantic.plugin import Plugin


class OnValidatePython(_OnValidatePython):
    def enter(
        self,
        input: Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, Any] | None = None,
        self_instance: Any | None = None,
    ) -> None:
        pprint(input)

    def on_success(self, result: Any) -> None:
        pprint(result)

    def on_error(self, error: ValidationError) -> None:
        pprint(error.json())


plugin = Plugin(on_validate_python=OnValidatePython)
```

[schema validator]: pydantic_core.SchemaValidator
[validate python]: pydantic_core.SchemaValidator.validate_python
[validate json]: pydantic_core.SchemaValidator.validate_json
