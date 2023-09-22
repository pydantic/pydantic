from __future__ import annotations

import sys
import warnings
from typing import TYPE_CHECKING, Iterable

from typing_extensions import Final

if sys.version_info >= (3, 8):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata


if TYPE_CHECKING:
    from . import PydanticPluginProtocol


PYDANTIC_ENTRY_POINT_GROUP: Final[str] = 'pydantic'

_plugins: dict[str, PydanticPluginProtocol] = {}


def get_plugins() -> Iterable[PydanticPluginProtocol]:
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
            except (ImportError, AttributeError) as e:
                error_type = e.__class__.__name__
                warnings.warn(
                    f'{error_type} while loading the `{entry_point.name}` Pydantic plugin, this could be caused '
                    f'by a circular import issue (e.g. the plugin importing Pydantic), Pydantic will attempt to '
                    f'import this plugin again each time a Pydantic validators is created. {e}'
                )

    return _plugins.values()
