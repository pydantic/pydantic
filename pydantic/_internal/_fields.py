"""
Private logic related to fields (the `Field()` function and `FieldInfo` class), and arguments to `Annotated`.
"""
from __future__ import annotations as _annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic_core import core_schema

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


class BaseSelfType:
    """
    No-op marker class for `self` type reference.

    All the weird logic here is for the purposes of handling recursive generics.
    Note this _must_ be a type for it to work properly during evaluation as a ForwardRef.
    We need __class_getitem__ to work because that gets called on generic types.
    """

    self_schema: ClassVar[core_schema.CoreSchema]
    model: ClassVar[type[BaseModel]]
    class_getitems: ClassVar[list[Any]]

    @classmethod
    def __class_getitem__(cls, item: Any) -> Any:
        updated_class_getitems = cls.class_getitems + [item]

        class SelfType(cls):  # type: ignore[valid-type,misc]
            class_getitems = updated_class_getitems

        return SelfType


def get_self_type(self_schema_: core_schema.CoreSchema, model_: type[BaseModel]) -> type[BaseSelfType]:
    class SelfType(BaseSelfType):
        self_schema = self_schema_
        model = model_
        class_getitems = []

    return SelfType


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
