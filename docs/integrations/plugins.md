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

Consider that you have a plugin called `pydantic_plugin`, then you can use it like this:

```py test="skip"
from pydantic import BaseModel


class Foo(BaseModel, pydantic_plugin='all'):
    ...
```

On each validation call, a callable registered for the event `all` will be called with the
instance of `Foo`, the event name, and the validation result.
