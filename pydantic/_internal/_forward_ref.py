from __future__ import annotations as _annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Union

from pydantic_core import core_schema
from typing_extensions import Literal, TypedDict

from ._typing_extra import TypeVarType

if TYPE_CHECKING:
    from ..main import BaseModel


class DeferredClassGetitem(TypedDict):
    kind: Literal['class_getitem']
    item: Any


class DeferredReplaceTypes(TypedDict):
    kind: Literal['replace_types']
    typevars_map: dict[TypeVarType, Any]


DeferredAction = Union[DeferredClassGetitem, DeferredReplaceTypes]


@dataclass
class PydanticForwardRef:
    """
    No-op marker class for (recursive) type references.

    Most of the logic here exists to handle recursive generics.
    """

    schema: core_schema.CoreSchema
    model: type[BaseModel]

    __name__ = 'PydanticForwardRef'
    __hash__ = object.__hash__

    def __call__(self) -> None:
        """
        Defining __call__ is necessary for the `typing` module to let you use an instance of
        this class as the result of resolving a standard ForwardRef
        """

    def __getitem__(self, item: Any) -> PydanticForwardRef:
        return self.model.__class_getitem__(item)
