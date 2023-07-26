"""This module is used to load plugins for pydantic.

Plugins are installed via Python entry points, for example in `pyproject.toml`:

```toml
[project.entry-points.pydantic]
pydantic_sdk = "pydantic_sdk:main"
```

The entry point group is `pydantic` and the name of the entry point is the name of the plugin.

On Pydantic, plugins are loaded by calling `load_plugins()`. Plugins are loaded in the order
they are found, and the order they are found is not guaranteed.

Consider that you have a plugin called setting called "observer", then you can use it like this:

```py
from pydantic import BaseModel

class Foo(BaseModel, plugin_settings={'observer': 'all'}):
    ...
```

On each validation call, the `plugin_settings` will be passed to a callable registered for the
events.
"""
from __future__ import annotations

import sys

from typing_extensions import Final

from .plugin import Plugin

if sys.version_info >= (3, 8):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata


GROUP: Final[str] = 'pydantic'


def load_plugins() -> list[Plugin]:
    """Load plugins for pydantic.

    Inspired by:
    - https://github.com/pytest-dev/pytest/blob/5c0e5aa39916e6a49962e662002c23f578e897c9/src/pluggy/_manager.py#L352-L377
    """
    plugins: list[Plugin] = []
    for dist in importlib_metadata.distributions():
        for entry_point in dist.entry_points:
            if entry_point.group == GROUP:
                plugins.append(entry_point.load())
    return plugins


plugins = load_plugins()
