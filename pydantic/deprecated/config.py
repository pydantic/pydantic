from __future__ import annotations as _annotations

import warnings
from typing import TYPE_CHECKING, Any, Literal

from typing_extensions import deprecated

from ..warnings import PydanticDeprecatedSince20

if not TYPE_CHECKING:
    # See PyCharm issues https://youtrack.jetbrains.com/issue/PY-21915
    # and https://youtrack.jetbrains.com/issue/PY-51428
    DeprecationWarning = PydanticDeprecatedSince20

__all__ = ('Extra',)


class _ExtraMeta(type):
    def __getattribute__(self, __name: str) -> Any:
        # The @deprecated decorator accesses other attributes, so we only emit a warning for the expected ones
        if __name in {'allow', 'ignore', 'forbid'}:
            warnings.warn(
                "`pydantic.config.Extra` is deprecated, use literal values instead (e.g. `extra='allow'`)",
                DeprecationWarning,
                stacklevel=2,
            )
        return super().__getattribute__(__name)


@deprecated(
    "Extra is deprecated. Use literal values instead (e.g. `extra='allow'`)", category=PydanticDeprecatedSince20
)
class Extra(metaclass=_ExtraMeta):
    allow: Literal['allow'] = 'allow'
    ignore: Literal['ignore'] = 'ignore'
    forbid: Literal['forbid'] = 'forbid'
