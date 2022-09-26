from __future__ import annotations as _annotations

from typing import Any, TypeVar

T = TypeVar('T')


class UndefinedType:
    def __repr__(self) -> str:
        return 'PydanticUndefined'

    def __copy__(self: T) -> T:
        return self

    def __reduce__(self) -> str:
        return 'Undefined'

    def __deepcopy__(self: T, _: Any) -> T:
        return self


class PydanticMetadata:
    """
    Base class for annotation markers like `Strict`.
    """

    __slots__ = ()


class CustomMetadata(PydanticMetadata):
    def __init__(self, **metadata):
        self.__dict__ = metadata
