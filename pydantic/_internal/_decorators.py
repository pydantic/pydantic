"""Logic related to validators applied to models etc. via the `@field_validator` and `@root_validator` decorators."""
from __future__ import annotations as _annotations

from collections import deque
from dataclasses import dataclass, field
from functools import partial, partialmethod
from inspect import Parameter, Signature, isdatadescriptor, ismethoddescriptor, signature
from itertools import islice
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generic, Iterable, TypeVar, Union

from pydantic_core import core_schema
from typing_extensions import Literal, TypeAlias, is_typeddict

from ..errors import PydanticUserError
from ..fields import ComputedFieldInfo
from ._core_utils import get_type_ref
from ._internal_dataclass import slots_dataclass
from ._typing_extra import get_function_type_hints

if TYPE_CHECKING:
    from ..functional_validators import FieldValidatorModes

try:
    from functools import cached_property  # type: ignore
except ImportError:
    # python 3.7
    cached_property = None


@slots_dataclass
class ValidatorDecoratorInfo:
    """A container for data from `@validator` so that we can access it
    while building the pydantic-core schema.

    Attributes:
        decorator_repr: A class variable representing the decorator string, '@validator'.
        fields: A tuple of field names the validator should be called on.
        mode: The proposed validator mode.
        each_item: For complex objects (sets, lists etc.) whether to validate individual
            elements rather than the whole object.
        always: Whether this method and other validators should be called even if the value is missing.
        check_fields: Whether to check that the fields actually exist on the model.
    """

    decorator_repr: ClassVar[str] = '@validator'

    fields: tuple[str, ...]
    mode: Literal['before', 'after']
    each_item: bool
    always: bool
    check_fields: bool | None


@slots_dataclass
class FieldValidatorDecoratorInfo:
    """A container for data from `@field_validator` so that we can access it
    while building the pydantic-core schema.

    Attributes:
        decorator_repr: A class variable representing the decorator string, '@field_validator'.
        fields: A tuple of field names the validator should be called on.
        mode: The proposed validator mode.
        check_fields: Whether to check that the fields actually exist on the model.
    """

    decorator_repr: ClassVar[str] = '@field_validator'

    fields: tuple[str, ...]
    mode: FieldValidatorModes
    check_fields: bool | None


@slots_dataclass
class RootValidatorDecoratorInfo:
    """A container for data from `@root_validator` so that we can access it
    while building the pydantic-core schema.

    Attributes:
        decorator_repr: A class variable representing the decorator string, '@root_validator'.
        mode: The proposed validator mode.
    """

    decorator_repr: ClassVar[str] = '@root_validator'
    mode: Literal['before', 'after']


@slots_dataclass
class FieldSerializerDecoratorInfo:
    """A container for data from `@field_serializer` so that we can access it
    while building the pydantic-core schema.

    Attributes:
        decorator_repr: A class variable representing the decorator string, '@field_serializer'.
        fields: A tuple of field names the serializer should be called on.
        mode: The proposed serializer mode.
        return_type: The type of the serializer's return value.
        when_used: The serialization condition. Accepts a string with values `'always'`, `'unless-none'`, `'json'`,
            and `'json-unless-none'`.
        check_fields: Whether to check that the fields actually exist on the model.
    """

    decorator_repr: ClassVar[str] = '@field_serializer'
    fields: tuple[str, ...]
    mode: Literal['plain', 'wrap']
    return_type: Any
    when_used: core_schema.WhenUsed
    check_fields: bool | None


@slots_dataclass
class ModelSerializerDecoratorInfo:
    """A container for data from `@model_serializer` so that we can access it
    while building the pydantic-core schema.

    Attributes:
        decorator_repr: A class variable representing the decorator string, '@model_serializer'.
        mode: The proposed serializer mode.
        return_type: The type of the serializer's return value.
        when_used: The serialization condition. Accepts a string with values `'always'`, `'unless-none'`, `'json'`,
            and `'json-unless-none'`.
    """

    decorator_repr: ClassVar[str] = '@model_serializer'
    mode: Literal['plain', 'wrap']
    return_type: Any
    when_used: core_schema.WhenUsed


@slots_dataclass
class ModelValidatorDecoratorInfo:
    """A container for data from `@model_validator` so that we can access it
    while building the pydantic-core schema.

    Attributes:
        decorator_repr: A class variable representing the decorator string, '@model_serializer'.
        mode: The proposed serializer mode.
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
    """Wrap a classmethod, staticmethod, property or unbound function
    and act as a descriptor that allows us to detect decorated items
    from the class' attributes.

    This class' __get__ returns the wrapped item's __get__ result,
    which makes it transparent for classmethods and staticmethods.

    Attributes:
        wrapped: The decorator that has to be wrapped.
        decorator_info: The decorator info.
        shim: A wrapper function to wrap V1 style function.
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
        """Forward checks for __isabstractmethod__ and such."""
        return getattr(self.wrapped, __name)


DecoratorInfoType = TypeVar('DecoratorInfoType', bound=DecoratorInfo)


@slots_dataclass
class Decorator(Generic[DecoratorInfoType]):
    """A generic container class to join together the decorator metadata
    (metadata from decorator itself, which we have when the
    decorator is called but not when we are building the core-schema)
    and the bound function (which we have after the class itself is created).

    Attributes:
        cls_ref: The class ref.
        cls_var_name: The decorated function name.
        func: The decorated function.
        shim: A wrapper function to wrap V1 style function.
        info: The decorator info.
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
        """Build a new decorator.

        Args:
            cls_: The class.
            cls_var_name: The decorated function name.
            shim: A wrapper function to wrap V1 style function.
            info: The decorator info.

        Returns:
            The new decorator instance.
        """
        func = get_attribute_from_bases(cls_, cls_var_name)
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
        """Bind the decorator to a class.

        Args:
            cls: the class.

        Returns:
            The new decorator instance.
        """
        return self.build(
            cls,
            cls_var_name=self.cls_var_name,
            shim=self.shim,
            info=self.info,
        )


def get_bases(tp: type[Any]) -> tuple[type[Any], ...]:
    """Get the base classes of a class or typeddict.

    Args:
        tp: The type or class to get the bases.

    Returns:
        The base classes.
    """
    if is_typeddict(tp):
        return tp.__orig_bases__  # type: ignore
    try:
        return tp.__bases__
    except AttributeError:
        return ()


def mro(tp: type[Any]) -> tuple[type[Any], ...]:
    """Calculate the Method Resolution Order of bases using the C3 algorithm.

    See https://www.python.org/download/releases/2.3/mro/
    """
    # try to use the existing mro, for performance mainly
    # but also because it helps verify the implementation below
    if not is_typeddict(tp):
        try:
            return tp.__mro__
        except AttributeError:
            # GenericAlias and some other cases
            pass

    def merge_seqs(seqs: list[deque[type[Any]]]) -> Iterable[type[Any]]:
        while True:
            non_empty = [seq for seq in seqs if seq]
            if not non_empty:
                # Nothing left to process, we're done.
                return
            candidate: type[Any] | None = None
            for seq in non_empty:  # Find merge candidates among seq heads.
                candidate = seq[0]
                not_head = [s for s in non_empty if candidate in islice(s, 1, None)]
                if not_head:
                    # Reject the candidate.
                    candidate = None
                else:
                    break
            if not candidate:
                raise TypeError('Inconsistent hierarchy, no C3 MRO is possible')
            yield candidate
            for seq in non_empty:
                # Remove candidate.
                if seq[0] == candidate:
                    seq.popleft()

    bases = get_bases(tp)
    seqs = [deque(mro(base)) for base in bases] + [deque(bases)]
    res = tuple(merge_seqs(seqs))

    return (tp,) + res


def get_attribute_from_bases(tp: type[Any], name: str) -> Any:
    """Get the attribute from the next class in the MRO that has it,
    aiming to simulate calling the method on the actual class.

    The reason for iterating over the mro instead of just getting
    the attribute (which would do that for us) is to support TypedDict,
    which lacks a real __mro__, but can have a virtual one constructed
    from its bases (as done here).

    Args:
        tp: The type or class to search for the attribute.
        name: The name of the attribute to retrieve.

    Returns:
        Any: The attribute value, if found.

    Raises:
        AttributeError: If the attribute is not found in any class in the MRO.
    """
    try:
        return getattr(tp, name)
    except Exception as e:
        for base in reversed(mro(tp)):
            if hasattr(base, name):
                return getattr(base, name)
        raise e


@slots_dataclass
class DecoratorInfos:
    """Mapping of name in the class namespace to decorator info.

    note that the name in the class namespace is the function or attribute name
    not the field name!
    """

    validators: dict[str, Decorator[ValidatorDecoratorInfo]] = field(default_factory=dict)
    field_validators: dict[str, Decorator[FieldValidatorDecoratorInfo]] = field(default_factory=dict)
    root_validators: dict[str, Decorator[RootValidatorDecoratorInfo]] = field(default_factory=dict)
    field_serializers: dict[str, Decorator[FieldSerializerDecoratorInfo]] = field(default_factory=dict)
    model_serializers: dict[str, Decorator[ModelSerializerDecoratorInfo]] = field(default_factory=dict)
    model_validators: dict[str, Decorator[ModelValidatorDecoratorInfo]] = field(default_factory=dict)
    computed_fields: dict[str, Decorator[ComputedFieldInfo]] = field(default_factory=dict)

    @staticmethod
    def build(model_dc: type[Any]) -> DecoratorInfos:  # noqa: C901 (ignore complexity)
        """We want to collect all DecFunc instances that exist as
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
        for base in reversed(mro(model_dc)[1:]):
            existing: DecoratorInfos | None = base.__dict__.get('__pydantic_decorators__')
            if existing is None:
                existing = DecoratorInfos.build(base)
            res.validators.update({k: v.bind_to_cls(model_dc) for k, v in existing.validators.items()})
            res.field_validators.update({k: v.bind_to_cls(model_dc) for k, v in existing.field_validators.items()})
            res.root_validators.update({k: v.bind_to_cls(model_dc) for k, v in existing.root_validators.items()})
            res.field_serializers.update({k: v.bind_to_cls(model_dc) for k, v in existing.field_serializers.items()})
            res.model_serializers.update({k: v.bind_to_cls(model_dc) for k, v in existing.model_serializers.items()})
            res.model_validators.update({k: v.bind_to_cls(model_dc) for k, v in existing.model_validators.items()})
            res.computed_fields.update({k: v.bind_to_cls(model_dc) for k, v in existing.computed_fields.items()})

        to_replace: list[tuple[str, Any]] = []

        for var_name, var_value in vars(model_dc).items():
            if isinstance(var_value, PydanticDescriptorProxy):
                info = var_value.decorator_info
                if isinstance(info, ValidatorDecoratorInfo):
                    res.validators[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                elif isinstance(info, FieldValidatorDecoratorInfo):
                    res.field_validators[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                elif isinstance(info, RootValidatorDecoratorInfo):
                    res.root_validators[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                elif isinstance(info, FieldSerializerDecoratorInfo):
                    # check whether a serializer function is already registered for fields
                    for field_serializer_decorator in res.field_serializers.values():
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
                    res.field_serializers[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                elif isinstance(info, ModelValidatorDecoratorInfo):
                    res.model_validators[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                elif isinstance(info, ModelSerializerDecoratorInfo):
                    res.model_serializers[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=var_value.shim, info=info
                    )
                else:
                    isinstance(var_value, ComputedFieldInfo)
                    res.computed_fields[var_name] = Decorator.build(
                        model_dc, cls_var_name=var_name, shim=None, info=info
                    )
                to_replace.append((var_name, var_value.wrapped))
        if to_replace:
            # If we can save `__pydantic_decorators__` on the class we'll be able to check for it above
            # so then we don't need to re-process the type, which means we can discard our descriptor wrappers
            # and replace them with the thing they are wrapping (see the other setattr call below)
            # which allows validator class methods to also function as regular class methods
            setattr(model_dc, '__pydantic_decorators__', res)
            for name, value in to_replace:
                setattr(model_dc, name, value)
        return res


def inspect_validator(validator: Callable[..., Any], mode: FieldValidatorModes) -> bool:
    """Look at a field or model validator function and determine if it whether it takes an info argument.

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
    """Look at a field serializer function and determine if it is a field serializer,
    and whether it takes an info argument.

    An error is raised if the function has an invalid signature.

    Args:
        serializer: The serializer function to inspect.
        mode: The serializer mode, either 'plain' or 'wrap'.

    Returns:
        Tuple of (is_field_serializer, info_arg).
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
    """Look at a serializer function used via `Annotated` and determine whether it takes an info argument.

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
    """Look at a model serializer function and determine whether it takes an info argument.

    An error is raised if the function has an invalid signature.

    Args:
        serializer: The serializer function to check.
        mode: The serializer mode, either 'plain' or 'wrap'.

    Returns:
        `info_arg` - whether the function expects an info argument.
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
    """Whether the function is an instance method.

    It will consider a function as instance method if the first parameter of
    function is `self`.

    Args:
        function: The function to check.

    Returns:
        `True` if the function is an instance method, `False` otherwise.
    """
    sig = signature(unwrap_wrapped_function(function))
    first = next(iter(sig.parameters.values()), None)
    if first and first.name == 'self':
        return True
    return False


def ensure_classmethod_based_on_signature(function: AnyDecoratorCallable) -> Any:
    """Apply the `@classmethod` decorator on the function.

    Args:
        function: The function to apply the decorator on.

    Return:
        The `@classmethod` decorator applied function.
    """
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
    """Recursively unwraps a wrapped function until the underlying function is reached.
    This handles functools.partial, functools.partialmethod, staticmethod and classmethod.

    Args:
        func: The function to unwrap.
        unwrap_class_static_method: If True (default), also unwrap classmethod and staticmethod
            decorators. If False, only unwrap partial and partialmethod decorators.

    Returns:
        The underlying function of the wrapped function.
    """
    all: set[Any] = {partial, partialmethod, property}

    try:
        from functools import cached_property  # type: ignore
    except ImportError:
        cached_property = type('', (), {})  # type: ignore
    else:
        all.add(cached_property)

    if unwrap_class_static_method:
        all.update({staticmethod, classmethod})

    while isinstance(func, tuple(all)):
        if unwrap_class_static_method and isinstance(func, (classmethod, staticmethod)):
            func = func.__func__
        elif isinstance(func, (partial, partialmethod)):
            func = func.func
        elif isinstance(func, property):
            func = func.fget  # arbitrary choice, convenient for computed fields
        else:
            # Make coverage happy as it can only get here in the last possible case
            assert isinstance(func, cached_property)
            func = func.func  # type: ignore

    return func


def get_function_return_type(func: Any, explicit_return_type: Any) -> Any:
    """Get the function return type.

    It gets the return type from the type annotation if `explicit_return_type` is `None`.
    Otherwise, it returns `explicit_return_type`.

    Args:
        func: The function to get its return type.
        explicit_return_type: The explicit return type.

    Returns:
        The function return type.
    """
    if explicit_return_type is None:
        # try to get it from the type annotation
        func = unwrap_wrapped_function(func)
        hints = get_function_type_hints(unwrap_wrapped_function(func), include_keys={'return'})
        return hints.get('return', None)
    else:
        return explicit_return_type


def count_positional_params(sig: Signature) -> int:
    return sum(1 for param in sig.parameters.values() if can_be_positional(param))


def can_be_positional(param: Parameter) -> bool:
    return param.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)


def ensure_property(f: Any) -> Any:
    """Ensure that a function is a `property` or `cached_property`, or is a valid descriptor.

    Args:
        f: The function to check.

    Returns:
        The function, or a `property` or `cached_property` instance wrapping the function.
    """
    if ismethoddescriptor(f) or isdatadescriptor(f):
        return f
    else:
        return property(f)
