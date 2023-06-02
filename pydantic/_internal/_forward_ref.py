from __future__ import annotations as _annotations

from dataclasses import dataclass
from typing import Any, Union

from typing_extensions import Literal, TypedDict

from ._typing_extra import TypeVarType


class DeferredClassGetitem(TypedDict):
    kind: Literal['class_getitem']
    item: Any


class DeferredReplaceTypes(TypedDict):
    kind: Literal['replace_types']
    typevars_map: dict[TypeVarType, Any]


DeferredAction = Union[DeferredClassGetitem, DeferredReplaceTypes]


@dataclass
class PydanticRecursiveRef:
    type_ref: str

    __name__ = 'PydanticRecursiveRef'
    __hash__ = object.__hash__

    def __call__(self) -> None:
        """
        Defining __call__ is necessary for the `typing` module to let you use an instance of
        this class as the result of resolving a standard ForwardRef
        """
