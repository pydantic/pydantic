"""
Private logic related to fields (the `Field()` function and `FieldInfo` class), and arguments to `Annotated`.
"""
from __future__ import annotations as _annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Literal, TypedDict, Union

from pydantic_core import core_schema

from ._generics import TypeVarType, replace_types
from ._repr import Representation

if TYPE_CHECKING:
    from pydantic import BaseModel


class _UndefinedType:
    """
    Singleton class to represent an undefined value.
    """

    def __repr__(self) -> str:
        return 'PydanticUndefined'

    def __copy__(self) -> '_UndefinedType':
        return self

    def __reduce__(self) -> str:
        return 'Undefined'

    def __deepcopy__(self, _: Any) -> '_UndefinedType':
        return self


Undefined = _UndefinedType()


class PydanticMetadata(Representation):
    """
    Base class for annotation markers like `Strict`.
    """

    __slots__ = ()


class PydanticGeneralMetadata(PydanticMetadata):
    def __init__(self, **metadata: Any):
        self.__dict__ = metadata


class SchemaRef(Representation):
    """
    Holds a reference to another schema.
    """

    __slots__ = ('__pydantic_core_schema__',)

    def __init__(self, schema: core_schema.CoreSchema):
        self.__pydantic_core_schema__ = schema


class CustomValidator(ABC):
    """
    Used to define functional validators which can be updated with constraints.
    """

    @abstractmethod
    def __pydantic_update_schema__(self, schema: core_schema.CoreSchema, **constraints: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    def __call__(self, __input_value: Any, **_kwargs: Any) -> Any:
        raise NotImplementedError()

    def _update_attrs(self, constraints: dict[str, Any], attrs: set[str] | None = None) -> None:
        """
        Utility for updating attributes/slots and raising an error if they don't exist, to be used by
        implementations of `CustomValidator`.
        """
        attrs = attrs or set(self.__slots__)  # type: ignore[attr-defined]
        for k, v in constraints.items():
            if k not in attrs:
                raise TypeError(f'{self.__class__.__name__} has no attribute {k!r}')
            setattr(self, k, v)


# TODO: Should all this self-type stuff go in a new file?
# TODO: Does it make sense to rename to RecursiveType or similar?
#   "SelfType" is a bit more of a confusing name once there are _multiple_ models in play (referencing themselves)
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


def get_self_type(
    self_schema_: core_schema.CoreSchema, model_: type[BaseModel], deferred_actions_: list[Any] | None = None
) -> type[BaseSelfType]:
    class SelfType(BaseSelfType):
        self_schema = self_schema_
        model = model_
        deferred_actions = deferred_actions_ or []

    return SelfType
