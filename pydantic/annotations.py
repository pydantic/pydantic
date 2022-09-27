from __future__ import annotations as _annotations

import dataclasses as _dataclasses
import typing as _typing

from ._internal import _annotations

__all__ = 'Strict', 'AllowInfNan'


@_dataclasses.dataclass
class Strict(_annotations.PydanticMetadata):
    strict: bool | None = True


@_dataclasses.dataclass
class AllowInfNan(_annotations.PydanticMetadata):
    strict: bool | None = True
