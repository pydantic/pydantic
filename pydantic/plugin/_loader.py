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
import warnings

from typing_extensions import Final

from .plugin import Plugin

if sys.version_info >= (3, 8):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata


GROUP: Final[str] = 'pydantic'

plugins: set[Plugin]

_plugins: dict[str, Plugin] = {}


def load_plugins():
    """Load plugins for pydantic.

    Inspired by:
    - https://github.com/pytest-dev/pytest/blob/5c0e5aa399(16e6a49962e662002c23f578e897c9/src/pluggy/_manager.py#L352-L377
    """
    global _plugins

    for dist in importlib_metadata.distributions():
        for entry_point in dist.entry_points:
            if entry_point.group != GROUP:
                continue
            if entry_point.value in _plugins:
                continue
            _plugins[entry_point.value] = entry_point.load()


def __getattr__(attr_name: str) -> object:
    global _plugins

    if attr_name != 'plugins':
        raise AttributeError(f'module {__name__!r} has no attribute {attr_name!r}')

    try:
        load_plugins()
    except ImportError:
        warnings.warn(
            'Import error while loading a Pydantic plugin could be caused by a circular import,'
            ' avoid module level imports from the same package in your plugin'
        )
        raise

    return set(_plugins.values())
