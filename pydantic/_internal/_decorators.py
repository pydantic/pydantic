"""
Logic related to validators applied to models etc. via the `@field_validator` and `@root_validator` decorators.
"""
from __future__ import annotations as _annotations

from dataclasses import dataclass, field
from functools import partial, partialmethod
from inspect import Parameter, Signature, isdatadescriptor, ismethoddescriptor, signature
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generic, TypeVar, Union, cast

from pydantic_core import core_schema
from typing_extensions import Literal, TypeAlias

from ..errors import PydanticUserError
from ..fields import ComputedFieldInfo
from ._core_utils import get_type_ref
from ._internal_dataclass import slots_dataclass

if TYPE_CHECKING:
    from ..validators import FieldValidatorModes

try:
    from functools import cached_property  # type: ignore
except ImportError:
    # python 3.7
    cached_property = None


@slots_dataclass
class ValidatorDecoratorInfo:
    """
    A container for data from `@validator` so that we can access it
    while building the pydantic-core schema.
    """

    decorator_repr: ClassVar[str] = '@validator'

    fields: tuple[str, ...]
    mode: Literal['before', 'after']
    each_item: bool
    always: bool
    check_fields: bool | None


@slots_dataclass
class FieldValidatorDecoratorInfo:
    """
    A container for data from `@field_validator` so that we can access it
    while building the pydantic-core schema.
    """

    decorator_repr: ClassVar[str] = '@field_validator'

    fields: tuple[str, ...]
    mode: FieldValidatorModes
    check_fields: bool | None


@slots_dataclass
class RootValidatorDecoratorInfo:
    """
    A container for data from `@root_validator` so that we can access it
    while building the pydantic-core schema.
    """

    decorator_repr: ClassVar[str] = '@root_validator'
    mode: Literal['before', 'after']


@slots_dataclass
class FieldSerializerDecoratorInfo:
    """
    A container for data from `@field_serializer` so that we can access it
    while building the pydantic-core schema.
    """

    decorator_repr: ClassVar[str] = '@field_serializer'
    fields: tuple[str, ...]
    mode: Literal['plain', 'wrap']
    json_return_type: core_schema.JsonReturnTypes | None
    when_used: core_schema.WhenUsed
    check_fields: bool | None


@slots_dataclass
class ModelSerializerDecoratorInfo:
    """
    A container for data from `@model_serializer` so that we can access it
    while building the pydantic-core schema.
    """

    decorator_repr: ClassVar[str] = '@model_serializer'
    mode: Literal['plain', 'wrap']
    json_return_type: core_schema.JsonReturnTypes | None


@slots_dataclass
class ModelValidatorDecoratorInfo:
    """
    A container for data from `@model_validator` so that we can access it
    while building the pydantic-core schema.
    """

    decorator_repr: ClassVar[str] = '@model_validator'
    mode: Literal['wrap', 'before', 'after']


DecoratorInfo = Union[
    ValidatorDecoratorInfo,
    FieldValidatorDecoratorInfo,
    RootValidatorDecoratorInfo,
    FieldSerializerDecoratorInfo,
    ModelSerializerDecoratorInfo,
    ModelValidatorDecoratorInfo,
    ComputedFieldInfo,
]

ReturnType = TypeVar('ReturnType')
DecoratedType: TypeAlias = (
    'Union[classmethod[Any, Any, ReturnType], staticmethod[Any, ReturnType], Callable[..., ReturnType], property]'
)


@dataclass  # can't use slots here since we set attributes on `__post_init__`
class PydanticDescriptorProxy(Generic[ReturnType]):
    """
    Wrap a classmethod, staticmethod, property or unbound function
    and act as a descriptor that allows us to detect decorated items
    from the class' attributes.

    This class' __get__ returns the wrapped item's __get__ result,
    which makes it transparent for classmethods and staticmethods.
    """

    wrapped: DecoratedType[ReturnType]
    decorator_info: DecoratorInfo
    shim: Callable[[Callable[..., Any]], Callable[..., Any]] | None = None

    def __post_init__(self):
        for attr in 'setter', 'deleter':
            if hasattr(self.wrapped, attr):
                f = partial(self._call_wrapped_attr, name=attr)
                setattr(self, attr, f)

    def _call_wrapped_attr(self, func: Callable[[Any], None], *, name: str) -> PydanticDescriptorProxy[ReturnType]:
        self.wrapped = getattr(self.wrapped, name)(func)
        return self

    def __get__(self, obj: object | None, obj_type: type[object] | None = None) -> PydanticDescriptorProxy[ReturnType]:
        try:
            return self.wrapped.__get__(obj, obj_type)
        except AttributeError:
            # not a descriptor, e.g. a partial object
            return self.wrapped  # type: ignore[return-value]

    def __set_name__(self, instance: Any, name: str) -> None:
        if hasattr(self.wrapped, '__set_name__'):
            self.wrapped.__set_name__(instance, name)

    def __getattr__(self, __name: str) -> Any:
        """Forward checks for __isabstractmethod__ and such"""
        return getattr(self.wrapped, __name)


DecoratorInfoType = TypeVar('DecoratorInfoType', bound=DecoratorInfo)


@slots_dataclass
class Decorator(Generic[DecoratorInfoType]):
    """
    A generic container class to join together the decorator metadata
    (metadata from decorator itself, which we have when the
    decorator is called but not when we are building the core-schema)
    and the bound function (which we have after the class itself is created).
    """

    cls_ref: str
    cls_var_name: str
    func: Callable[..., Any]
    shim: Callable[[Any], Any] | None
    info: DecoratorInfoType

    @staticmethod
    def build(
        cls_: Any,
        *,
        cls_var_name: str,
        shim: Callable[[Any], Any] | None,
        info: DecoratorInfoType,
    ) -> Decorator[DecoratorInfoType]:
        func = getattr(cls_, cls_var_name)
        if shim is not None:
            func = shim(func)
        return Decorator(
            cls_ref=get_type_ref(cls_),
            cls_var_name=cls_var_name,
            func=func,
            shim=shim,
            info=info,
        )

    def bind_to_cls(self, cls: Any) -> Decorator[DecoratorInfoType]:
        return self.build(
            cls,
            cls_var_name=self.cls_var_name,
            shim=self.shim,
            info=self.info,
        )


@slots_dataclass
class DecoratorInfos:
    # mapping of name in the class namespace to decorator info
    # note that the name in the class namespace is the function or attribute name
    # not the field name!
    # TODO these all need to be renamed to plural
    validator: dict[str, Decorator[ValidatorDecoratorInfo]] = field(default_factory=dict)
    field_validator: dict[str, Decorator[FieldValidatorDecoratorInfo]] = field(default_factory=dict)
    root_validator: dict[str, Decorator[RootValidatorDecoratorInfo]] = field(default_factory=dict)
    field_serializer: dict[str, Decorator[FieldSerializerDecoratorInfo]] = field(default_factory=dict)
    model_serializer: dict[str, Decorator[ModelSerializerDecoratorInfo]] = field(default_factory=dict)
    model_validator: dict[str, Decorator[ModelValidatorDecoratorInfo]] = field(default_factory=dict)
    computed_fields: dict[str, Decorator[ComputedFieldInfo]] = field(default_factory=dict)

    @staticmethod
    def build(model_dc: type[Any]) -> DecoratorInfos:  # noqa: C901 (ignore complexity)
        """
        We want to collect all DecFunc instances that exist as
        attributes in the namespace of the class (a BaseModel or dataclass)
        that called us
        But we want to collect these in the order of the bases
        So instead of getting them all from the leaf class (the class that called us),
        we traverse the bases from root (the oldest ancestor class) to leaf
        and collect all of the instances as we go, taking care to replace
        any duplicate ones with the last one we see to mimic how function overriding
        works with inheritance.
        If we do replace any functions we put the replacement into the position
        the replaced function was in; that is, we maintain the order.
        """

        # reminder: dicts are ordered and replacement does not alter the order
        res = DecoratorInfos()
        for base in model_dc.__bases__[::-1]:
            existing = cast(Union[DecoratorInfos, None], getattr(base, '__pydantic_decorators__', None))
            if existing is not None:
                res.validator.update({k: v.bind_to_cls(model_dc) for k, v in existing.validator.items()})
                res.field_validator.update({k: v.bind_to_cls(model_dc) for k, v in existing.field_validator.items()})
                res.root_validator.update({k: v.bind_to_cls(model_dc) for k, v in existing.root_validator.items()})
                res.field_serializer.update({k: v.bind_to_cls(model_dc) for k, v in existing.field_serializer.items()})
                res.model_serializer.update({k: v.bind_to_cls(model_dc) for k, v in existing.model_serializer.items()})
                res.model_validator.update({k: v.bind_to_cls(model_dc) for k, v in existing.model_validator.items()})
                res.computed_fields.update({k: v.bind_to_cls(model_dc) for k, v in existing.computed_fields.items()})

        for var_name, var_value in vars(model_dc).items():
            if isinstance(var_value, PydanticDescriptorProxy):
                info = var_value.decorator_info
                if isinstance(info, ValidatorDecoratorInfo):
                    res.validator[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                elif isinstance(info, FieldValidatorDecoratorInfo):
                    res.field_validator[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                elif isinstance(info, RootValidatorDecoratorInfo):
                    res.root_validator[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                elif isinstance(info, FieldSerializerDecoratorInfo):
                    # check whether a serializer function is already registered for fields
                    for field_serializer_decorator in res.field_serializer.values():
                        # check that each field has at most one serializer function.
                        # serializer functions for the same field in subclasses are allowed,
                        # and are treated as overrides
                        if field_serializer_decorator.cls_var_name == var_name:
                            continue
                        for f in info.fields:
                            if f in field_serializer_decorator.info.fields:
                                raise PydanticUserError(
                                    'Multiple field serializer functions were defined '
                                    f'for field {f!r}, this is not allowed.',
                                    code='multiple-field-serializers',
                                )
                    res.field_serializer[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                elif isinstance(info, ModelValidatorDecoratorInfo):
                    res.model_validator[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                elif isinstance(info, ModelSerializerDecoratorInfo):
                    res.model_serializer[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                else:
                    isinstance(var_value, ComputedFieldInfo)
                    res.computed_fields[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=None, info=info
                    )
                setattr(model_dc, var_name, var_value.wrapped)
        return res


def inspect_validator(validator: Callable[..., Any], mode: FieldValidatorModes) -> bool:
    """
    Look at a field or model validator function and determine if it whether it takes an info argument.

    An error is raised if the function has an invalid signature.

    Args:
        validator: The validator function to inspect.
        mode: The proposed validator mode.

    Returns:
        Whether the validator takes an info argument.
    """
    sig = signature(validator)
    n_positional = count_positional_params(sig)
    if mode == 'wrap':
        if n_positional == 3:
            return True
        elif n_positional == 2:
            return False
    else:
        assert mode in {'before', 'after', 'plain'}, f"invalid mode: {mode!r}, expected 'before', 'after' or 'plain"
        if n_positional == 2:
            return True
        elif n_positional == 1:
            return False

    raise PydanticUserError(
        f'Unrecognized field_validator function signature for {validator} with `mode={mode}`:{sig}',
        code='validator-signature',
    )


def inspect_field_serializer(serializer: Callable[..., Any], mode: Literal['plain', 'wrap']) -> tuple[bool, bool]:
    """
    Look at a field serializer function and determine if it is a field serializer,
    and whether it takes an info argument.

    An error is raised if the function has an invalid signature.

    Args:
        serializer: The serializer function to inspect.
        mode: The serializer mode, either 'plain' or 'wrap'.

    Returns:
        Tuple of (is_field_serializer, info_arg)
    """
    sig = signature(serializer)

    first = next(iter(sig.parameters.values()), None)
    is_field_serializer = first is not None and first.name == 'self'

    n_positional = count_positional_params(sig)
    if is_field_serializer:
        # -1 to correct for self parameter
        info_arg = _serializer_info_arg(mode, n_positional - 1)
    else:
        info_arg = _serializer_info_arg(mode, n_positional)

    if info_arg is None:
        raise PydanticUserError(
            f'Unrecognized field_serializer function signature for {serializer} with `mode={mode}`:{sig}',
            code='field-serializer-signature',
        )
    else:
        return is_field_serializer, info_arg


def inspect_annotated_serializer(serializer: Callable[..., Any], mode: Literal['plain', 'wrap']) -> bool:
    """
    Look at a serializer function used via `Annotated` and determine whether it takes an info argument.

    An error is raised if the function has an invalid signature.

    Args:
        serializer: The serializer function to check.
        mode: The serializer mode, either 'plain' or 'wrap'.

    Returns:
        info_arg
    """
    sig = signature(serializer)
    info_arg = _serializer_info_arg(mode, count_positional_params(sig))
    if info_arg is None:
        raise PydanticUserError(
            f'Unrecognized field_serializer function signature for {serializer} with `mode={mode}`:{sig}',
            code='field-serializer-signature',
        )
    else:
        return info_arg


def inspect_model_serializer(serializer: Callable[..., Any], mode: Literal['plain', 'wrap']) -> bool:
    """
    Look at a model serializer function and determine whether it takes an info argument.

    An error is raised if the function has an invalid signature.

    Args:
        serializer: The serializer function to check.
        mode: The serializer mode, either 'plain' or 'wrap'.

    Returns:
        `info_arg` - whether the function expects an info argument
    """

    if isinstance(serializer, (staticmethod, classmethod)) or not is_instance_method_from_sig(serializer):
        raise PydanticUserError(
            '`@model_serializer` must be applied to instance methods', code='model-serializer-instance-method'
        )

    sig = signature(serializer)
    info_arg = _serializer_info_arg(mode, count_positional_params(sig))
    if info_arg is None:
        raise PydanticUserError(
            f'Unrecognized model_serializer function signature for {serializer} with `mode={mode}`:{sig}',
            code='model-serializer-signature',
        )
    else:
        return info_arg


def _serializer_info_arg(mode: Literal['plain', 'wrap'], n_positional: int) -> bool | None:
    if mode == 'plain':
        if n_positional == 1:
            # (__input_value: Any) -> Any
            return False
        elif n_positional == 2:
            # (__model: Any, __input_value: Any) -> Any
            return True
    else:
        assert mode == 'wrap', f"invalid mode: {mode!r}, expected 'plain' or 'wrap'"
        if n_positional == 2:
            # (__input_value: Any, __serializer: SerializerFunctionWrapHandler) -> Any
            return False
        elif n_positional == 3:
            # (__input_value: Any, __serializer: SerializerFunctionWrapHandler, __info: SerializationInfo) -> Any
            return True

    return None


AnyDecoratorCallable: TypeAlias = (
    'Union[classmethod[Any, Any, Any], staticmethod[Any, Any], partialmethod[Any], Callable[..., Any]]'
)


def is_instance_method_from_sig(function: AnyDecoratorCallable) -> bool:
    sig = signature(unwrap_wrapped_function(function))
    first = next(iter(sig.parameters.values()), None)
    if first and first.name == 'self':
        return True
    return False


def ensure_classmethod_based_on_signature(function: AnyDecoratorCallable) -> Any:
    if not isinstance(
        unwrap_wrapped_function(function, unwrap_class_static_method=False), classmethod
    ) and _is_classmethod_from_sig(function):
        return classmethod(function)  # type: ignore[arg-type]
    return function


def _is_classmethod_from_sig(function: AnyDecoratorCallable) -> bool:
    sig = signature(unwrap_wrapped_function(function))
    first = next(iter(sig.parameters.values()), None)
    if first and first.name == 'cls':
        return True
    return False


def unwrap_wrapped_function(
    func: Any,
    *,
    unwrap_class_static_method: bool = True,
) -> Any:
    """
    Recursively unwraps a wrapped function until the underlying function is reached.
    This handles functools.partial, functools.partialmethod, staticmethod and classmethod.

    Args:
        func: The function to unwrap.
        unwrap_class_static_method: If True (default), also unwrap classmethod and staticmethod
            decorators. If False, only unwrap partial and partialmethod decorators.

    Returns:
        The underlying function of the wrapped function.
    """
    all: tuple[Any, ...]
    if unwrap_class_static_method:
        all = (
            staticmethod,
            classmethod,
            partial,
            partialmethod,
        )
    else:
        all = partial, partialmethod

    while isinstance(func, all):
        if unwrap_class_static_method and isinstance(func, (classmethod, staticmethod)):
            func = func.__func__
        elif isinstance(func, (partial, partialmethod)):
            func = func.func

    return func


def count_positional_params(sig: Signature) -> int:
    return sum(1 for param in sig.parameters.values() if can_be_positional(param))


def can_be_positional(param: Parameter) -> bool:
    return param.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)


def ensure_property(f: Any) -> Any:
    """
    Ensure that a function is a `property` or `cached_property`, or is a valid descriptor.

    Args:
        f: The function to check.

    Returns:
        The function, or a `property` or `cached_property` instance wrapping the function.
    """

    if ismethoddescriptor(f) or isdatadescriptor(f):
        return f
    else:
        return property(f)
