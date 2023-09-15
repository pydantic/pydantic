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
from typing import Iterable

from typing_extensions import Final

from .plugin import PydanticPlugin

if sys.version_info >= (3, 8):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata


ENTRY_POINT_GROUP: Final[str] = 'pydantic'

_plugins: dict[str, PydanticPlugin] = {}


def get_plugins() -> Iterable[PydanticPlugin]:
    """Load plugins for pydantic.

    Inspired by:
    - https://github.com/pytest-dev/pytest/blob/5c0e5aa399(16e6a49962e662002c23f578e897c9/src/pluggy/_manager.py#L352-L377
    """
    global _plugins

    for dist in importlib_metadata.distributions():
        for entry_point in dist.entry_points:
            if entry_point.group != ENTRY_POINT_GROUP:
                continue
            if entry_point.value in _plugins:
                continue
            try:
                _plugins[entry_point.value] = entry_point.load()
            except ImportError as e:
                warnings.warn(
                    f'Import error while loading "{entry_point.name}" Pydantic plugin could be caused by a circular'
                    f' import, Pydantic will attempt importing this plugin again after other imports are finished. {e}'
                )

    return _plugins.values()
