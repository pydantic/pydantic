"""
Private logic related to fields (the `Field()` function and `FieldInfo` class), and arguments to `Annotated`.
"""
from __future__ import annotations as _annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic_core import core_schema

from ._repr import Representation


class PydanticMetadata:
    """
    Base class for annotation markers like `Strict`.
    """

    __slots__ = ()


class CustomMetadata(Representation, PydanticMetadata):
    def __init__(self, **metadata: Any):
        self.__dict__ = metadata


class SchemaRef(PydanticMetadata):
    """
    Holds a reference to another schema.
    """

    __slots__ = '_name', '__pydantic_validation_schema__'

    def __init__(self, name: str, core_schema: core_schema.CoreSchema):
        self._name = name
        self.__pydantic_validation_schema__ = core_schema

    def __repr__(self) -> str:
        return f'SchemaRef({self._name!r}, {self.__pydantic_validation_schema__})'


class CustomValidator(ABC):
    @abstractmethod
    def __pydantic_update_schema__(self, schema: core_schema.CoreSchema, **constraints: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    def __call__(self, __input_value: Any, **_kwargs: Any) -> Any:
        raise NotImplementedError()

    def _update_attrs(self, constraints: dict[str, Any], attrs: set[str] | None = None) -> None:
        attrs = attrs or set(self.__slots__)  # type: ignore[attr-defined]
        for k, v in constraints.items():
            if k not in attrs:
                raise TypeError(f'{self.__class__.__name__} has no attribute {k!r}')
            setattr(self, k, v)
