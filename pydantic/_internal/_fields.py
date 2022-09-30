from __future__ import annotations as _annotations

from typing import Any, TypeVar

from pydantic_core import CoreSchema

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
    def __init__(self, **metadata: Any):
        self.__dict__ = metadata


class SchemaRef(PydanticMetadata):
    """
    Holds a reference to another schema.
    """

    __slots__ = '_name', '__pydantic_validation_schema__'

    def __init__(self, name: str, core_schema: CoreSchema):
        self._name = name
        self.__pydantic_validation_schema__ = core_schema

    def __repr__(self) -> str:
        return f'SchemaRef({self._name!r}, {self.__pydantic_validation_schema__})'
