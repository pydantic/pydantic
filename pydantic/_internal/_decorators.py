"""
Logic related to validators applied to models etc. via the `@validator` and `@root_validator` decorators.
"""
from __future__ import annotations as _annotations

from dataclasses import field
from functools import partial, partialmethod
from inspect import Parameter, Signature, signature
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)

from pydantic_core.core_schema import (
    FieldPlainSerializerFunction,
    FieldValidationInfo,
    FieldValidatorFunction,
    FieldWrapSerializerFunction,
    FieldWrapValidatorFunction,
    GeneralPlainSerializerFunction,
    GeneralWrapSerializerFunction,
    JsonReturnTypes,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    ValidationInfo,
    WhenUsed,
)
from typing_extensions import Literal, Protocol, TypeAlias

from ..errors import PydanticUserError
from ._core_utils import get_type_ref
from ._internal_dataclass import slots_dataclass

FIELD_VALIDATOR_TAG = '_field_validator'
ROOT_VALIDATOR_TAG = '_root_validator'

FIELD_SERIALIZER_TAG = '_field_serializer'


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
    mode: Literal['before', 'after', 'wrap', 'plain']
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
    type: Literal['general', 'field']
    json_return_type: JsonReturnTypes | None
    when_used: WhenUsed
    check_fields: bool | None


@slots_dataclass
class ModelSerializerDecoratorInfo:
    """
    A container for data from `@model_serializer` so that we can access it
    while building the pydantic-core schema.
    """

    decorator_repr: ClassVar[str] = '@model_serializer'
    mode: Literal['plain', 'wrap']
    json_return_type: JsonReturnTypes | None


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
]

ReturnType = TypeVar('ReturnType')
DecoratedType: TypeAlias = (
    'Union[classmethod[Any, Any, ReturnType], staticmethod[Any, ReturnType], Callable[..., ReturnType]]'
)


@slots_dataclass
class PydanticDecoratorMarker(Generic[ReturnType]):
    """
    Wrap a classmethod, staticmethod or unbound function
    and act as a descriptor that allows us to detect decorated items
    from the class' attributes.

    This class' __get__ returns the wrapped item's __get__ result,
    which makes it transparent for classmethods and staticmethods.
    """

    wrapped: DecoratedType[ReturnType]
    decorator_info: DecoratorInfo
    shim: Callable[[Callable[..., Any]], Callable[..., Any]] | None

    @overload
    def __get__(self, obj: None, objtype: None) -> PydanticDecoratorMarker[ReturnType]:
        ...

    @overload
    def __get__(self, obj: object, objtype: type[object]) -> Callable[..., ReturnType]:
        ...

    def __get__(
        self, obj: object | None, objtype: type[object] | None = None
    ) -> Callable[..., ReturnType] | PydanticDecoratorMarker[ReturnType]:
        try:
            return self.wrapped.__get__(obj, objtype)
        except AttributeError:
            # not a descriptor, e.g. a partial object
            return self.wrapped  # type: ignore[return-value]


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
    validator: dict[str, Decorator[ValidatorDecoratorInfo]] = field(default_factory=dict)
    field_validator: dict[str, Decorator[FieldValidatorDecoratorInfo]] = field(default_factory=dict)
    root_validator: dict[str, Decorator[RootValidatorDecoratorInfo]] = field(default_factory=dict)
    field_serializer: dict[str, Decorator[FieldSerializerDecoratorInfo]] = field(default_factory=dict)
    model_serializer: dict[str, Decorator[ModelSerializerDecoratorInfo]] = field(default_factory=dict)
    model_validator: dict[str, Decorator[ModelValidatorDecoratorInfo]] = field(default_factory=dict)


def gather_decorator_functions(cls: type[Any]) -> DecoratorInfos:
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
    for base in cls.__bases__[::-1]:
        existing = cast(Union[DecoratorInfos, None], getattr(base, '__pydantic_decorators__', None))
        if existing is not None:
            res.validator.update({k: v.bind_to_cls(cls) for k, v in existing.validator.items()})
            res.field_validator.update({k: v.bind_to_cls(cls) for k, v in existing.field_validator.items()})
            res.root_validator.update({k: v.bind_to_cls(cls) for k, v in existing.root_validator.items()})
            res.field_serializer.update({k: v.bind_to_cls(cls) for k, v in existing.field_serializer.items()})
            res.model_serializer.update({k: v.bind_to_cls(cls) for k, v in existing.model_serializer.items()})

    for var_name, var_value in vars(cls).items():
        if isinstance(var_value, PydanticDecoratorMarker):
            info = var_value.decorator_info
            if isinstance(info, ValidatorDecoratorInfo):
                res.validator[var_name] = Decorator.build(cls, cls_var_name=var_name, shim=var_value.shim, info=info)
            elif isinstance(info, FieldValidatorDecoratorInfo):
                res.field_validator[var_name] = Decorator.build(
                    cls, cls_var_name=var_name, shim=var_value.shim, info=info
                )
            elif isinstance(info, RootValidatorDecoratorInfo):
                res.root_validator[var_name] = Decorator.build(
                    cls, cls_var_name=var_name, shim=var_value.shim, info=info
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
                    cls, cls_var_name=var_name, shim=var_value.shim, info=info
                )
            elif isinstance(info, ModelValidatorDecoratorInfo):
                res.model_validator[var_name] = Decorator.build(
                    cls, cls_var_name=var_name, shim=var_value.shim, info=info
                )
            else:
                assert isinstance(info, ModelSerializerDecoratorInfo)
                res.model_serializer[var_name] = Decorator.build(
                    cls, cls_var_name=var_name, shim=var_value.shim, info=info
                )
            setattr(cls, var_name, var_value.wrapped)
    return res


_FUNCS: set[str] = set()


AnyDecoratorCallable: TypeAlias = (
    'Union[classmethod[Any, Any, Any], staticmethod[Any, Any], partialmethod[Any], Callable[..., Any]]'
)


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


def get_function_ref(func: Any) -> str:
    func = unwrap_wrapped_function(func)
    return (
        getattr(func, '__module__', '<No __module__>')
        + '.'
        + getattr(func, '__qualname__', f'<No __qualname__: id:{id(func)}>')
    )


def is_classmethod_from_sig(function: AnyDecoratorCallable) -> bool:
    sig = signature(unwrap_wrapped_function(function))
    first = next(iter(sig.parameters.values()), None)
    if first and first.name == 'cls':
        return True
    return False


def is_instance_method_from_sig(function: AnyDecoratorCallable) -> bool:
    sig = signature(unwrap_wrapped_function(function))
    first = next(iter(sig.parameters.values()), None)
    if first and first.name == 'self':
        return True
    return False


def ensure_classmethod_based_on_signature(
    function: AnyDecoratorCallable,
) -> Any:
    if not isinstance(
        unwrap_wrapped_function(function, unwrap_class_static_method=False), classmethod
    ) and is_classmethod_from_sig(function):
        return classmethod(function)  # type: ignore[arg-type]
    return function


class OnlyValueValidator(Protocol):
    """
    A simple validator, supported for V1 validators and V2 validators
    """

    def __call__(self, __value: Any) -> Any:
        ...


class V1ValidatorWithValues(Protocol):
    def __call__(self, __value: Any, values: dict[str, Any]) -> Any:
        ...


class V1ValidatorWithValuesKwOnly(Protocol):
    def __call__(self, __value: Any, *, values: dict[str, Any]) -> Any:
        ...


class V1ValidatorWithKwargs(Protocol):
    def __call__(self, __value: Any, **kwargs: Any) -> Any:
        ...


class V1ValidatorWithValuesAndKwargs(Protocol):
    def __call__(self, __value: Any, values: dict[str, Any], **kwargs: Any) -> Any:
        ...


V1Validator = Union[
    V1ValidatorWithValues, V1ValidatorWithValuesKwOnly, V1ValidatorWithKwargs, V1ValidatorWithValuesAndKwargs
]


def can_be_positional(param: Parameter) -> bool:
    return param.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)


def can_be_keyword(param: Parameter) -> bool:
    return param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)


def make_generic_v1_field_validator(validator: V1Validator) -> FieldValidatorFunction:
    sig = signature(validator)

    needs_values_kw = False

    for param_num, (param_name, parameter) in enumerate(sig.parameters.items()):
        if can_be_keyword(parameter) and param_name in ('field', 'config'):
            raise PydanticUserError(
                'The `field` and `config` parameters are not available in Pydantic V2, '
                'please use the `info` parameter instead.',
                code='validator-field-config-info',
            )
        if parameter.kind is Parameter.VAR_KEYWORD:
            needs_values_kw = True
        elif can_be_keyword(parameter) and param_name == 'values':
            needs_values_kw = True
        elif can_be_positional(parameter) and param_num == 0:
            # value
            continue
        elif parameter.default is Parameter.empty:  # ignore params with defaults e.g. bound by functools.partial
            raise PydanticUserError(
                f'Unsupported signature for V1 style validator {validator}: {sig} is not supported.',
                code='validator-v1-signature',
            )

    if needs_values_kw:
        # (v, **kwargs), (v, values, **kwargs), (v, *, values, **kwargs) or (v, *, values)
        val1 = cast(V1ValidatorWithValues, validator)

        def wrapper1(value: Any, info: FieldValidationInfo) -> Any:
            return val1(value, values=info.data)

        return wrapper1
    else:
        val2 = cast(OnlyValueValidator, validator)

        def wrapper2(value: Any, _: FieldValidationInfo) -> Any:
            return val2(value)

        return wrapper2


def remove_params_with_defaults(sig: Signature) -> Signature:
    return Signature([p for p in sig.parameters.values() if p.default is Parameter.empty])


def make_generic_validator(
    validator: OnlyValueValidator | FieldValidatorFunction | FieldWrapValidatorFunction, mode: str
) -> Any:
    """
    In order to support different signatures, including deprecated validator signatures from v1,
    we introspect the function signature and wrap it in a parent function that has a signature
    compatible with pydantic_core
    """
    sig = remove_params_with_defaults(signature(validator))
    if mode in ('before', 'after', 'plain') and len(sig.parameters) == 1:
        val1 = cast(OnlyValueValidator, validator)

        # allow the (v) -> Any signature as a convenience
        def wrapper1(value: Any, info: FieldValidationInfo) -> Any:
            return val1(value)

        return wrapper1

    val2 = cast(Union[FieldValidatorFunction, FieldWrapValidatorFunction], validator)
    return val2


RootValidatorValues = Dict[str, Any]
RootValidatorFieldsSet = Set[str]
RootValidatorValuesAndFieldsSet = Tuple[RootValidatorValues, RootValidatorFieldsSet]


class V1RootValidatorFunction(Protocol):
    def __call__(self, __values: RootValidatorValues) -> RootValidatorValues:
        ...


class V2CoreBeforeRootValidator(Protocol):
    def __call__(self, __values: RootValidatorValues, __info: ValidationInfo) -> RootValidatorValues:
        ...


class V2CoreAfterRootValidator(Protocol):
    def __call__(
        self, __values_and_fields_set: RootValidatorValuesAndFieldsSet, __info: ValidationInfo
    ) -> RootValidatorValuesAndFieldsSet:
        ...


def make_v1_generic_root_validator(
    validator: V1RootValidatorFunction, pre: bool
) -> V2CoreBeforeRootValidator | V2CoreAfterRootValidator:
    """
    Wrap a V1 style root validator for V2 compatibility
    """
    if pre is True:
        # mode='before' for pydantic-core
        def _wrapper1(values: RootValidatorValues, _: ValidationInfo) -> RootValidatorValues:
            return validator(values)

        return _wrapper1

    # mode='after' for pydantic-core
    def _wrapper2(
        values_and_fields_set: tuple[RootValidatorValues, RootValidatorFieldsSet], _: ValidationInfo
    ) -> tuple[RootValidatorValues, RootValidatorFieldsSet]:
        values, fields_set = values_and_fields_set
        values = validator(values)
        return (values, fields_set)

    return _wrapper2


GenericPlainSerializerFunctionWithoutInfo = Callable[[Any], Any]
FieldPlainSerializerFunctionWithoutInfo = Callable[[Any, Any], Any]
FieldWrapSerializerFunctionWithoutInfo = Callable[[Any, Any, SerializerFunctionWrapHandler], Any]
GeneralWrapSerializerFunctionWithoutInfo = Callable[[Any, SerializerFunctionWrapHandler], Any]

AnyCoreSerializer = Union[
    FieldPlainSerializerFunction,
    FieldWrapSerializerFunction,
    GeneralPlainSerializerFunction,
    GeneralWrapSerializerFunction,
]

AnySerializerFunction = Union[
    GenericPlainSerializerFunctionWithoutInfo,
    GeneralWrapSerializerFunctionWithoutInfo,
    AnyCoreSerializer,
]


def make_generic_serializer(
    serializer: AnySerializerFunction, mode: Literal['plain', 'wrap'], type: Literal['field', 'general']
) -> Any:
    """
    Wrap serializers to allow ignoring the `info` argument as a convenience.
    """
    sig = remove_params_with_defaults(signature(serializer))
    if is_instance_method_from_sig(serializer):
        # for the errors below to exclude self
        sig = Signature(parameters=list(sig.parameters.values())[1:])

    n_positional = sum(
        1
        for param in sig.parameters.values()
        if param.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
    )
    if mode == 'plain':
        if n_positional == 1:
            if type == 'general':
                func1 = cast(GenericPlainSerializerFunctionWithoutInfo, serializer)

                def wrap_generic_serializer_single_argument(value: Any, _: SerializationInfo) -> Any:
                    return func1(value)

                return wrap_generic_serializer_single_argument
            else:
                assert type == 'field'
                func2 = cast(FieldPlainSerializerFunctionWithoutInfo, serializer)

                def wrap_field_serializer_single_argument(self: Any, value: Any, _: SerializationInfo) -> Any:
                    return func2(self, value)

                return wrap_field_serializer_single_argument
        if n_positional != 2:
            raise PydanticUserError(
                f'Unrecognized field_serializer signature for {serializer} with `mode={mode}`:{sig}',
                code='field-serializer-signature',
            )
        func = cast(AnyCoreSerializer, serializer)
        return func
    else:
        assert mode == 'wrap'
        if n_positional == 2:
            if type == 'general':
                func3 = cast(GeneralWrapSerializerFunctionWithoutInfo, serializer)

                def wrap_general_serializer_in_wrap_mode(
                    value: Any, handler: SerializerFunctionWrapHandler, _: SerializationInfo
                ) -> Any:
                    return func3(value, handler)

                return wrap_general_serializer_in_wrap_mode
            else:
                assert type == 'field'
                func4 = cast(FieldWrapSerializerFunctionWithoutInfo, serializer)

                def wrap_field_serializer_in_wrap_mode(
                    self: Any, value: Any, handler: SerializerFunctionWrapHandler, _: SerializationInfo
                ) -> Any:
                    return func4(self, value, handler)

                return wrap_field_serializer_in_wrap_mode

        if n_positional != 3:
            raise PydanticUserError(
                f'Unrecognized field_serializer signature for {serializer} with `mode={mode}`:{sig}',
                code='field-serializer-signature',
            )
        func = cast(AnyCoreSerializer, serializer)
        return func


def make_generic_model_serializer(
    serializer: AnySerializerFunction, mode: Literal['plain', 'wrap']
) -> AnyCoreSerializer:
    """
    Wrap serializers to allow ignoring the `info` argument as a convenience.
    """
    sig = signature(serializer)

    n_positional = sum(
        1
        for param in sig.parameters.values()
        if param.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
    )
    if mode == 'plain':
        if n_positional == 1:
            func1 = cast(GenericPlainSerializerFunctionWithoutInfo, serializer)

            def wrap_model_serializer_single_argument(value: Any, _: SerializationInfo) -> Any:
                return func1(value)

            return wrap_model_serializer_single_argument
        if n_positional != 2:
            raise PydanticUserError(
                f'Unrecognized model_serializer signature for {serializer} with `mode={mode}`:{sig}',
                code='model-serializer-signature',
            )
        func = cast(AnyCoreSerializer, serializer)
        return func
    else:
        assert mode == 'wrap'
        if n_positional == 2:
            func2 = cast(GeneralWrapSerializerFunctionWithoutInfo, serializer)

            def wrap_model_serializer_in_wrap_mode(
                value: Any, handler: SerializerFunctionWrapHandler, _: SerializationInfo
            ) -> Any:
                return func2(value, handler)

            return wrap_model_serializer_in_wrap_mode

        if n_positional != 3:
            raise PydanticUserError(
                f'Unrecognized serializer signature for {serializer} with `mode={mode}`:{sig}',
                code='model-serializer-signature',
            )
        func = cast(AnyCoreSerializer, serializer)
        return func
