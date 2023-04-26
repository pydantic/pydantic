from __future__ import annotations as _annotations

from dataclasses import dataclass, replace
from typing import Any, Union

from pydantic_core import core_schema
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


@dataclass
class PydanticForwardRef:
    """
    No-op marker class for (recursive) type references.

    Most of the logic here exists to handle recursive generics.
    """

    schema: core_schema.CoreSchema
    model: type[Any]
    deferred_actions: tuple[DeferredAction, ...] = ()

    __name__ = 'PydanticForwardRef'
    __hash__ = object.__hash__

    def __call__(self) -> None:
        """
        Defining __call__ is necessary for the `typing` module to let you use an instance of
        this class as the result of resolving a standard ForwardRef
        """

    def __getitem__(self, item: Any) -> PydanticForwardRef:
        updated_actions = self.deferred_actions + ({'kind': 'class_getitem', 'item': item},)
        return replace(self, deferred_actions=updated_actions)

    def replace_types(self, typevars_map: Any) -> PydanticForwardRef:
        updated_actions = self.deferred_actions + ({'kind': 'replace_types', 'typevars_map': typevars_map},)
        return replace(self, deferred_actions=updated_actions)

    def resolve_model(self) -> type[Any] | PydanticForwardRef:
        from ._generics import replace_types

        model: type[Any] | PydanticForwardRef = self.model
        for action in self.deferred_actions:
            if action['kind'] == 'replace_types':
                model = replace_types(model, action['typevars_map'])
            elif action['kind'] == 'class_getitem':
                model = model[action['item']]  # type: ignore[index]
            else:
                raise ValueError(f'Unexpected action: {action}')
        return model
