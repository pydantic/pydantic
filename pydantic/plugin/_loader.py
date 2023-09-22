from __future__ import annotations

import sys
import warnings
from typing import Iterable

from typing_extensions import Final

from ._types import PydanticPlugin

if sys.version_info >= (3, 8):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata


PYDANTIC_ENTRY_POINT_GROUP: Final[str] = 'pydantic'

_plugins: dict[str, PydanticPlugin] = {}


def get_plugins() -> Iterable[PydanticPlugin]:
    """Load plugins for Pydantic.

    Inspired by: https://github.com/pytest-dev/pluggy/blob/1.3.0/src/pluggy/_manager.py#L376-L402
    """
    global _plugins

    for dist in importlib_metadata.distributions():
        for entry_point in dist.entry_points:
            if entry_point.group != PYDANTIC_ENTRY_POINT_GROUP:
                continue
            if entry_point.value in _plugins:
                continue
            try:
                _plugins[entry_point.value] = entry_point.load()
            except ImportError as e:
                warnings.warn(
                    f'Import error while loading the `{entry_point.name}` Pydantic plugin, this could be caused '
                    f'by a circular import issue (e.g. the plugin importing Pydantic), Pydantic will attempt to '
                    f'import this plugin again each time a Pydantic validators is created. {e}'
                )

    return _plugins.values()
