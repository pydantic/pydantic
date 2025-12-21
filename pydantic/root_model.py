"""RootModel class and type definitions."""

from __future__ import annotations as _annotations

from copy import copy, deepcopy
from typing import TYPE_CHECKING, Any, Callable, Generic, Literal, TypeVar

from pydantic_core import PydanticUndefined
from typing_extensions import Self, dataclass_transform

from . import PydanticUserError
from ._internal import _model_construction, _repr
from .main import BaseModel, _object_setattr

if TYPE_CHECKING:
    from .fields import Field as PydanticModelField
    from .fields import PrivateAttr as PydanticModelPrivateAttr

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
        _object_setattr(m, '__dict__', copy(self.__dict__))
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

    @staticmethod
    def _process_include_exclude(param: Any) -> Any:
        """Transform `__root__` key to apply to root value's items.

        For RootModel, when the user specifies `__root__` in the
        include/exclude dict, they want to filter items within the root
        value. Since RootModel serializes directly to its root value,
        we extract the value of `__root__` and use it as the top-level
        include/exclude parameter.

        Args:
            param: The include or exclude parameter that may contain
                a `__root__` key.

        Returns:
            The transformed parameter with `__root__` value extracted.
        """
        if param is None:
            return None

        # Handle dict-like parameters
        if isinstance(param, dict):
            if '__root__' in param:
                # If __root__ is the only key, return its value directly
                # This allows {'__root__': {'__all__': {'b'}}} to become
                # {'__all__': {'b'}}, which filters all items in the list
                if len(param) == 1:
                    return param['__root__']
                # If there are other keys too, keep them but use root's
                # value for the 'root' field
                else:
                    root_value = param['__root__']
                    new_param = {k: v for k, v in param.items() if k != '__root__'}
                    new_param['root'] = root_value
                    return new_param

        return param

    def model_dump(
        self,
        *,
        mode: Literal['json', 'python'] | str = 'python',
        include: Any = None,
        exclude: Any = None,
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
    ) -> Any:
        """Generate a dictionary representation of the model.

        For `RootModel`, the `__root__` key can be used in `include` and
        `exclude` parameters to apply filtering to items within the root
        value (e.g., elements in a list or dict).

        See the documentation of `BaseModel.model_dump` for more details
        about the arguments.
        """
        # Transform __root__ to root in include/exclude parameters
        include = self._process_include_exclude(include)
        exclude = self._process_include_exclude(exclude)

        return super().model_dump(
            mode=mode,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            exclude_computed_fields=exclude_computed_fields,
            round_trip=round_trip,
            warnings=warnings,
            fallback=fallback,
            serialize_as_any=serialize_as_any,
        )

    def model_dump_json(
        self,
        *,
        indent: int | None = None,
        ensure_ascii: bool = False,
        include: Any = None,
        exclude: Any = None,
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
    ) -> str:
        """Generate a JSON representation of the model.

        For `RootModel`, the `__root__` key can be used in `include` and
        `exclude` parameters to apply filtering to items within the root
        value (e.g., elements in a list or dict).

        See the documentation of `BaseModel.model_dump_json` for more
        details about the arguments.
        """
        # Transform __root__ to root in include/exclude parameters
        include = self._process_include_exclude(include)
        exclude = self._process_include_exclude(exclude)

        return super().model_dump_json(
            indent=indent,
            ensure_ascii=ensure_ascii,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            exclude_computed_fields=exclude_computed_fields,
            round_trip=round_trip,
            warnings=warnings,
            fallback=fallback,
            serialize_as_any=serialize_as_any,
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RootModel):
            return NotImplemented
        return self.__pydantic_fields__['root'].annotation == other.__pydantic_fields__[
            'root'
        ].annotation and super().__eq__(other)

    def __repr_args__(self) -> _repr.ReprArgs:
        yield 'root', self.root
