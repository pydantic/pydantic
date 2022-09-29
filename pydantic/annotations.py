from __future__ import annotations as _annotations

import dataclasses as _dataclasses

from ._internal import _fields

__all__ = 'Strict', 'AllowInfNan'


@_dataclasses.dataclass
class Strict(_fields.PydanticMetadata):
    strict: bool | None = True


@_dataclasses.dataclass
class AllowInfNan(_fields.PydanticMetadata):
    strict: bool | None = True
