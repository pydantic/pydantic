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
