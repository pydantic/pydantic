from __future__ import annotations as _annotations

import typing

from ._internal import _repr
from .main import BaseModel

if typing.TYPE_CHECKING:
    from typing import Any

    Model = typing.TypeVar('Model', bound='BaseModel')


__all__ = ('RootModel',)


RootModelRootType = typing.TypeVar('RootModelRootType')


class RootModel(BaseModel, typing.Generic[RootModelRootType]):
    """A Pydantic `BaseModel` for the root object of the model.

    Attributes:
        root (RootModelRootType): The root object of the model.
    """

    __pydantic_root_model__ = True
    # TODO: Make `__pydantic_fields_set__` logic consistent with `BaseModel`, i.e. it should be `set()` if default value
    # was used
    __pydantic_fields_set__ = {'root'}  # It's fine having a set here as it will never change
    __pydantic_private__ = None
    __pydantic_extra__ = None

    root: RootModelRootType

    def __init__(__pydantic_self__, root: RootModelRootType) -> None:  # type: ignore
        __tracebackhide__ = True
        __pydantic_self__.__pydantic_validator__.validate_python(root, self_instance=__pydantic_self__)

    __init__.__pydantic_base_init__ = True  # type: ignore

    @classmethod
    def model_construct(cls: type[Model], root: RootModelRootType, _fields_set: set[str] | None = None) -> Model:
        """Create a new model using the provided root object and update fields set.

        Args:
            root: The root object of the model.
            _fields_set: The set of fields to be updated.

        Returns:
            The new model.

        Raises:
            NotImplemented: If the model is not a subclass of `RootModel`.
        """
        return super().model_construct(root=root, _fields_set=_fields_set)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RootModel):
            return NotImplemented
        return self.model_fields['root'].annotation == other.model_fields['root'].annotation and super().__eq__(other)

    def __repr_args__(self) -> _repr.ReprArgs:
        yield 'root', self.root
