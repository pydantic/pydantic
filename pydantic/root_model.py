"""RootModel class and type definitions."""

from __future__ import annotations as _annotations

from collections.abc import Callable
from copy import copy, deepcopy
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar

from pydantic_core import PydanticUndefined
from typing_extensions import Self, dataclass_transform

from . import PydanticUserError
from ._internal import _model_construction, _repr
from .main import BaseModel, _object_setattr

if TYPE_CHECKING:
    from .fields import Field as PydanticModelField
    from .fields import PrivateAttr as PydanticModelPrivateAttr
    from .main import IncEx

    # dataclass_transform could be applied to RootModel directly, but `ModelMetaclass`'s dataclass_transform
    # takes priority (at least with pyright). We trick type checkers into thinking we apply dataclass_transform
    # on a new metaclass.
    @dataclass_transform(kw_only_default=False, field_specifiers=(PydanticModelField, PydanticModelPrivateAttr))
    class _RootModelMetaclass(_model_construction.ModelMetaclass): ...
else:
    _RootModelMetaclass = _model_construction.ModelMetaclass

__all__ = ('RootModel',)

RootModelRootType = TypeVar('RootModelRootType')


class RootModel(BaseModel, Generic[RootModelRootType], metaclass=_RootModelMetaclass):
    """!!! abstract "Usage Documentation"
        [`RootModel` and Custom Root Types](../concepts/models.md#rootmodel-and-custom-root-types)

    A Pydantic `BaseModel` for the root object of the model.

    Attributes:
        root: The root object of the model.
        __pydantic_root_model__: Whether the model is a RootModel.
        __pydantic_private__: Private fields in the model.
        __pydantic_extra__: Extra fields in the model.

    """

    __pydantic_root_model__ = True
    __pydantic_private__ = None
    __pydantic_extra__ = None

    root: RootModelRootType

    def __init_subclass__(cls, **kwargs):
        extra = cls.model_config.get('extra')
        if extra is not None:
            raise PydanticUserError(
                "`RootModel` does not support setting `model_config['extra']`", code='root-model-extra'
            )
        super().__init_subclass__(**kwargs)

    def __init__(self, /, root: RootModelRootType = PydanticUndefined, **data) -> None:  # type: ignore
        __tracebackhide__ = True
        if data:
            if root is not PydanticUndefined:
                raise ValueError(
                    '"RootModel.__init__" accepts either a single positional argument or arbitrary keyword arguments'
                )
            root = data  # type: ignore
        self.__pydantic_validator__.validate_python(root, self_instance=self)

    __init__.__pydantic_base_init__ = True  # pyright: ignore[reportFunctionMemberAccess]

    @classmethod
    def model_construct(cls, root: RootModelRootType, _fields_set: set[str] | None = None) -> Self:  # type: ignore
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

    def __getstate__(self) -> dict[Any, Any]:
        return {
            '__dict__': self.__dict__,
            '__pydantic_fields_set__': self.__pydantic_fields_set__,
        }

    def __setstate__(self, state: dict[Any, Any]) -> None:
        _object_setattr(self, '__pydantic_fields_set__', state['__pydantic_fields_set__'])
        _object_setattr(self, '__dict__', state['__dict__'])

    def __copy__(self) -> Self:
        """Returns a shallow copy of the model."""
        cls = type(self)
        m = cls.__new__(cls)
        new_dict = copy(self.__dict__)
        new_dict['root'] = copy(self.__dict__['root'])  # pyright: ignore[reportIndexIssue] (https://github.com/microsoft/pyright/issues/11548)
        _object_setattr(m, '__dict__', new_dict)
        _object_setattr(m, '__pydantic_fields_set__', copy(self.__pydantic_fields_set__))
        return m

    def __deepcopy__(self, memo: dict[int, Any] | None = None) -> Self:
        """Returns a deep copy of the model."""
        cls = type(self)
        m = cls.__new__(cls)
        _object_setattr(m, '__dict__', deepcopy(self.__dict__, memo=memo))
        # This next line doesn't need a deepcopy because __pydantic_fields_set__ is a set[str],
        # and attempting a deepcopy would be marginally slower.
        _object_setattr(m, '__pydantic_fields_set__', copy(self.__pydantic_fields_set__))
        return m

    if TYPE_CHECKING:
        # This `model_dump()` definition is only provided to get a more accurate return type for type checkers
        # (no override is actually necessary at runtime). Generally, the return type will be `RootModelRootType`,
        # assuming that `RootModelRootType` is not a `BaseModel` subclass. If `RootModelRootType` is a `BaseModel`
        # subclass, then the return type will likely be `dict[str, Any]`, as `model_dump()` calls are recursive.
        # The return type could even be something different, in the case of a custom serializer. Thus, `Any` is
        # used here to catch all of these cases.

        def model_dump(  # type: ignore
            self,
            *,
            mode: Literal['json', 'python'] | str = 'python',
            include: IncEx | None = None,
            exclude: IncEx | None = None,
            context: Any | None = None,
            by_alias: bool | None = None,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            exclude_computed_fields: bool = False,
            round_trip: bool = False,
            warnings: bool | Literal['none', 'warn', 'error'] = True,
            fallback: Callable[[Any], Any] | None = None,
            serialize_as_any: bool = False,
            polymorphic_serialization: bool | None = None,
        ) -> Any:
            """!!! abstract "Usage Documentation"
                [`model_dump`](../concepts/serialization.md#python-mode)

            Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

            Args:
                mode: The mode in which `to_python` should run.
                    If mode is 'json', the output will only contain JSON serializable types.
                    If mode is 'python', the output may contain non-JSON-serializable Python objects.
                include: A set of fields to include in the output.
                exclude: A set of fields to exclude from the output.
                context: Additional context to pass to the serializer.
                by_alias: Whether to use the field's alias in the dictionary key if defined.
                exclude_unset: Whether to exclude fields that have not been explicitly set.
                exclude_defaults: Whether to exclude fields that are set to their default value.
                exclude_none: Whether to exclude fields that have a value of `None`.
                exclude_computed_fields: Whether to exclude computed fields.
                    While this can be useful for round-tripping, it is usually recommended to use the dedicated
                    `round_trip` parameter instead.
                round_trip: If True, dumped values should be valid as input for non-idempotent types such as Json[T].
                warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
                    "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
                fallback: A function to call when an unknown value is encountered. If not provided,
                    a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
                serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
                polymorphic_serialization: Whether to use model and dataclass polymorphic serialization for this call.

            Returns:
                A dictionary representation of the model.
            """
            ...

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RootModel):
            return NotImplemented
        return self.__pydantic_fields__['root'].annotation == other.__pydantic_fields__[
            'root'
        ].annotation and super().__eq__(other)

    def __repr_args__(self) -> _repr.ReprArgs:
        yield 'root', self.root
