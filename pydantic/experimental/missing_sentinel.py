"""Experimental module exposing the `MISSING` sentinel.

!!! warning "Deprecated"
    The `MISSING` sentinel is no longer experimental, and should be imported from the main `pydantic` module.
"""

import warnings
from typing import TYPE_CHECKING, Any

from ..warnings import PydanticDeprecatedSince214

if TYPE_CHECKING:
    from pydantic_core import MISSING

__all__ = ('MISSING',)


def __getattr__(name: str) -> Any:
    if name == 'MISSING':
        warnings.warn(
            'The `MISSING` sentinel is no longer experimental. Import it from the main `pydantic` module instead.',
            category=PydanticDeprecatedSince214,
            stacklevel=2,
        )
        from pydantic_core import MISSING

        return MISSING
    else:  # pragma: no cover
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
