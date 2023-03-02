from __future__ import annotations as _annotations

from typing import TYPE_CHECKING, Any, Union

from pydantic_core import core_schema
from typing_extensions import Literal, TypedDict, TypeGuard

from ._generics import TypeVarType, replace_types
from ._utils import lenient_issubclass

if TYPE_CHECKING:
    from pydantic import BaseModel


# TODO: Does it make sense to rename SelfType to RecursiveTypePlaceholder or similar?
#   "SelfType" is a bit more of a confusing name once there are _multiple_ models with placeholders in play
class SelfTypeClassGetitem(TypedDict):
    kind: Literal['class_getitem']
    item: Any


class SelfTypeReplaceTypes(TypedDict):
    kind: Literal['replace_types']
    typevars_map: dict[TypeVarType, Any]


SelfTypeAction = Union[SelfTypeClassGetitem, SelfTypeReplaceTypes]


class BaseSelfTypeMeta(type):
    """
    Because we are using BaseSelfType to hook into the python `typing` module's approach to
    resolving forward references and generic types, we end up treating BaseSelfType *subclasses*
    the way that you would handle instances in most "normal" code. This is necessary due to the
    fact that the `typing` module explicitly checks that forward references resolve to types,
    and also calls `__class_getitem__` on them when generic parameters are present.

    Using a custom metaclass lets us produce a debugging-friendly repr despite the fact that
    BaseSelfType and its subclasses never actually get instantiated.
    """

    model: type[BaseModel]
    deferred_actions: list[SelfTypeAction]
    self_schema: core_schema.CoreSchema

    def __repr__(self) -> str:
        return f'{self.__name__}(model={self.model}, actions={self.deferred_actions}, self_schema={self.self_schema})'


class BaseSelfType(metaclass=BaseSelfTypeMeta):
    """
    No-op marker class for `self` type reference.

    All the logic here exists to handle recursive generics.
    """

    @classmethod
    def __class_getitem__(cls, item: Any) -> Any:
        updated_actions = cls.deferred_actions + [{'kind': 'class_getitem', 'item': item}]

        class SelfType(BaseSelfType):
            model = cls.model
            deferred_actions = updated_actions
            self_schema = cls.self_schema

        return SelfType

    @classmethod
    def replace_types(cls, typevars_map: Any) -> type[BaseSelfType]:
        updated_actions = cls.deferred_actions + [{'kind': 'replace_types', 'typevars_map': typevars_map}]

        class SelfType(BaseSelfType):
            model = cls.model
            deferred_actions = updated_actions
            self_schema = cls.self_schema

        return SelfType

    @classmethod
    def resolve_model(cls) -> type[BaseSelfType] | type[BaseModel]:
        model: type[BaseModel] | type[BaseSelfType] = cls.model
        for action in cls.deferred_actions:
            if action['kind'] == 'replace_types':
                model = replace_types(model, action['typevars_map'])
            elif action['kind'] == 'class_getitem':
                model = model.__class_getitem__(action['item'])
        return model


def is_self_type(obj: Any) -> TypeGuard[type[BaseSelfType]]:
    """
    Using this typeguard instead of lenient_issubclass directly eliminates the need for casting
    for the sake of proper type-checking
    """
    return lenient_issubclass(obj, BaseSelfType)


def get_self_type(
    self_schema_: core_schema.CoreSchema, model_: type[BaseModel], deferred_actions_: list[Any] | None = None
) -> type[BaseSelfType]:
    class SelfType(BaseSelfType):
        self_schema = self_schema_
        model = model_
        deferred_actions = deferred_actions_ or []

    return SelfType
