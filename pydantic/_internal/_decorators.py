"""
Logic related to validators applied to models etc. via the `@validator` and `@root_validator` decorators.
"""
from __future__ import annotations as _annotations

import warnings
from inspect import Parameter, signature
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
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
    FieldValidationInfo,
    FieldValidatorFunction,
    FieldWrapValidatorFunction,
    JsonReturnTypes,
    ValidationInfo,
    WhenUsed,
)
from typing_extensions import Protocol, TypeAlias

from pydantic._internal._repr import Representation

if TYPE_CHECKING:
    from typing_extensions import Literal


FIELD_VALIDATOR_TAG = '_field_validator'
ROOT_VALIDATOR_TAG = '_root_validator'

FIELD_SERIALIZER_TAG = '_field_serializer'


class ValidatorDecoratorInfo(Representation):
    """
    A container for data from `@validator` so that we can access it
    while building the pydantic-core schema.
    """

    def __init__(
        self,
        *,
        fields: tuple[str, ...],
        # pre=True/False in v1 should be converted to mode='before'/'after' in v2
        mode: Literal['before', 'after'],
        check_fields: bool | None,
        each_item: bool,
    ) -> None:
        """
        :param mode: the pydantic-core validator mode.
        :param mode: Not yet supported.
        :param check_fields: whether to check that the fields actually exist on the model.
        """
        self.fields = fields
        self.mode = mode
        self.check_fields = check_fields
        self.each_item = each_item


class FieldValidatorDecoratorInfo(Representation):
    """
    A container for data from `@field_validator` so that we can access it
    while building the pydantic-core schema.
    """

    def __init__(
        self,
        *,
        fields: tuple[str, ...],
        mode: Literal['before', 'after', 'wrap', 'plain'],
        sub_path: tuple[str | int, ...] | None,
        check_fields: bool | None,
    ) -> None:
        """
        :param mode: the pydantic-core validator mode.
        :param type: either 'unbound' or 'field' indicating if this validator should have
            access to the model itself.
        :param mode: Not yet supported.
        :param check_fields: whether to check that the fields actually exist on the model.
        :param wrap: a callback to apply V1 compatibility shims or allow extra signatures
            that pydantic-core does not recognize.
        """
        self.fields = fields
        self.mode = mode
        self.sub_path = sub_path
        self.check_fields = check_fields


class RootValidatorDecoratorInfo(Representation):
    """
    A container for data from `@root_validator` so that we can access it
    while building the pydantic-core schema.
    """

    def __init__(
        self,
        *,
        mode: Literal['before', 'after'],
    ) -> None:
        """
        :param mode: the pydantic-core validator mode
        """
        self.mode = mode


class SerializerDecoratorInfo(Representation):
    """
    A container for data from `@serializer` so that we can access it
    while building the pydantic-core schema.
    """

    json_return_type: JsonReturnTypes | None
    when_used: WhenUsed

    def __init__(
        self,
        *,
        fields: tuple[str, ...],
        mode: Literal['plain', 'wrap'],
        json_return_type: JsonReturnTypes | None = None,
        when_used: WhenUsed = 'always',
        sub_path: tuple[str | int, ...] | None = None,
        check_fields: bool | None = None,
    ):
        self.fields = fields
        self.sub_path = sub_path
        self.mode = mode
        self.json_return_type = json_return_type
        self.when_used = when_used
        self.check_fields = check_fields


DecoratorInfo = Union[
    ValidatorDecoratorInfo, FieldValidatorDecoratorInfo, RootValidatorDecoratorInfo, SerializerDecoratorInfo
]

ReturnType = TypeVar('ReturnType')
DecoratedType: TypeAlias = 'Union[classmethod[ReturnType], staticmethod[ReturnType], Callable[..., ReturnType]]'


class PydanticDecoratorMarker(Generic[ReturnType], Representation):
    """
    Wrap a classmethod, staticmethod or unbound function
    and act as a descriptor that allows us to detect decorated items
    from the class' attributes.

    This class' __get__ returns the wrapped item's __get__ result,
    which makes it transparent for classmethods and staticmethods.
    """

    def __init__(
        self,
        wrapped: DecoratedType[ReturnType],
        decorator_info: DecoratorInfo,
        shim: Callable[[Callable[..., Any]], Callable[..., Any]] | None,
    ) -> None:
        self.wrapped = wrapped
        self.decorator_info = decorator_info
        self.shim = shim

    @overload
    def __get__(self, obj: None, objtype: None) -> PydanticDecoratorMarker[ReturnType]:
        ...

    @overload
    def __get__(self, obj: object, objtype: type[object]) -> Callable[..., ReturnType]:
        ...

    def __get__(
        self, obj: object | None, objtype: type[object] | None = None
    ) -> Callable[..., ReturnType] | PydanticDecoratorMarker[ReturnType]:
        if obj is None:
            return self
        return self.wrapped.__get__(obj, objtype)


DecoratorInfoType = TypeVar('DecoratorInfoType', bound=DecoratorInfo)


class Decorator(Generic[DecoratorInfoType], Representation):
    """
    A generic container class to join together the decorator metadata
    (metadata from decorator itself, which we have when the
    decorator is called but not when we are building the core-schema)
    and the bound function (which we have after the class itself is created).
    """

    def __init__(
        self,
        cls_var_name: str,
        func: Callable[..., Any],
        info: DecoratorInfoType,
    ) -> None:
        self.cls_var_name = cls_var_name
        self.func = func
        self.info = info


AnyDecorator = Union[
    Decorator[ValidatorDecoratorInfo],
    Decorator[FieldValidatorDecoratorInfo],
    Decorator[RootValidatorDecoratorInfo],
    Decorator[SerializerDecoratorInfo],
]


class DecoratorInfos(Representation):
    # mapping of name in the class namespace to decorator info
    # note that the name in the class namespace is the function or attribute name
    # not the field name!
    validator: dict[str, Decorator[ValidatorDecoratorInfo]]
    field_validator: dict[str, Decorator[FieldValidatorDecoratorInfo]]
    root_validator: dict[str, Decorator[RootValidatorDecoratorInfo]]
    serializer: dict[str, Decorator[SerializerDecoratorInfo]]

    def __init__(self) -> None:
        self.validator = {}
        self.field_validator = {}
        self.root_validator = {}
        self.serializer = {}


def gather_decorator_functions(cls: type[Any]) -> DecoratorInfos:
    # We want to collect all DecFunc instances that exist as
    # attributes in the namespace of the class (a BaseModel or dataclass)
    # that called us
    # But we want to collect these in the order of the bases
    # So instead of getting them all from the leaf class (the class that called us),
    # we traverse the bases from root (the oldest ancestor class) to leaf
    # and collect all of the instances as we go, taking care to replace
    # any duplicate ones with the last one we see to mimick how function overriding
    # works with inheritance.
    # If we do replace any functions we put the replacement into the position
    # the replaced function was in; that is, we maintain the order.

    # reminder: dicts are ordered and replacement does not alter the order
    res = DecoratorInfos()
    for base in cls.__bases__:
        existing = cast(Union[DecoratorInfos, None], getattr(base, '__pydantic_decorators__', None))
        if existing is not None:
            res.validator.update(existing.validator)
            res.field_validator.update(existing.field_validator)
            res.root_validator.update(existing.root_validator)
            res.serializer.update(existing.serializer)

    for var_name, var_value in vars(cls).items():
        if isinstance(var_value, PydanticDecoratorMarker):
            func = var_value.wrapped.__get__(None, cls)
            shimmed_func = var_value.shim(func) if var_value.shim is not None else func
            info = var_value.decorator_info
            if isinstance(info, ValidatorDecoratorInfo):
                res.validator[var_name] = Decorator(var_name, shimmed_func, info)
            elif isinstance(info, FieldValidatorDecoratorInfo):
                res.field_validator[var_name] = Decorator(var_name, shimmed_func, info)
            elif isinstance(info, RootValidatorDecoratorInfo):
                res.root_validator[var_name] = Decorator(var_name, shimmed_func, info)
            else:
                assert isinstance(info, SerializerDecoratorInfo)
                res.serializer[var_name] = Decorator(var_name, shimmed_func, info)
            # replace our marker with the bound, concrete function
            setattr(cls, var_name, func)

    return res


_FUNCS: set[str] = set()


_SerializerType = TypeVar('_SerializerType', bound=Callable[..., Any])


def prepare_serializer_decorator(function: _SerializerType, allow_reuse: bool) -> _SerializerType:
    """
    Warn about validators/serializers with duplicated names since without this, they can be overwritten silently
    which generally isn't the intended behaviour, don't run in ipython (see #312) or if `allow_reuse` is True.
    """
    if isinstance(function, staticmethod):
        function = function.__func__  # type: ignore[assignment]
    if not allow_reuse and not in_ipython():
        ref = f'{function.__module__}::{function.__qualname__}'
        if ref in _FUNCS:
            warnings.warn(f'duplicate validator function "{ref}"; if this is intended, set `allow_reuse=True`')
        _FUNCS.add(ref)
    return function


def unwrap_unbound_methods(function: Callable[..., Any] | classmethod[Any] | staticmethod[Any]) -> Callable[..., Any]:
    """
    Unwrap unbound classmethods and staticmethods
    """
    if isinstance(function, (classmethod, staticmethod)):
        return function.__func__
    return function


def is_v1_validator(function: Callable[..., Any] | staticmethod[Any] | classmethod[Any]) -> bool:
    """
    For the case where `@validator` is called with non of the `pre` or `mode` arguments
    determine if a function is a V1 validator or V2 validator.
    """
    sig = signature(unwrap_unbound_methods(function))
    # in V1 `values` had to be a keyword parameter
    # so we use that to distinguish (__v, values) from (__v, __info) or (__v, info)
    return any(
        pos != 0 and param.name == 'values' and param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY)
        for pos, param in enumerate(sig.parameters.values())
    ) or any(param.kind is Parameter.VAR_KEYWORD for param in sig.parameters.values())


def is_classmethod_from_sig(function: Callable[..., Any] | classmethod[Any] | staticmethod[Any]) -> bool:
    sig = signature(unwrap_unbound_methods(function))
    first = next(iter(sig.parameters.values()), None)
    if first and first.name == 'cls':
        return True
    return False


def is_instance_method_from_sig(function: Callable[..., Any] | classmethod[Any] | staticmethod[Any]) -> bool:
    sig = signature(unwrap_unbound_methods(function))
    first = next(iter(sig.parameters.values()), None)
    if first and first.name == 'self':
        return True
    return False


def ensure_classmethod_based_on_signature(
    function: Callable[..., Any] | classmethod[Any] | staticmethod[Any],
) -> classmethod[Any] | staticmethod[Any] | Callable[..., Any]:
    if not isinstance(function, classmethod) and is_classmethod_from_sig(function):
        return classmethod(function)
    return function


def check_for_duplicate_validator(
    function: Callable[..., Any] | classmethod[Any] | staticmethod[Any], allow_reuse: bool
) -> None:
    """
    Warn about validators with duplicated names since without this, they can be overwritten silently
    which generally isn't the intended behaviour, don't run in ipython (see #312) or if `allow_reuse` is True.
    """
    if not allow_reuse and not in_ipython():
        function = unwrap_unbound_methods(function)
        ref = f'{function.__module__}::{function.__qualname__}'
        if ref in _FUNCS:
            warnings.warn(f'duplicate validator function "{ref}"; if this is intended, set `allow_reuse=True`')
        _FUNCS.add(ref)


def in_ipython() -> bool:
    """
    Check whether we're in an ipython environment, including jupyter notebooks.
    """
    try:
        eval('__IPYTHON__')
    except NameError:
        return False
    else:  # pragma: no cover
        return True


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


V1_VALIDATOR_VALID_SIGNATURES = """\
def f1(value: Any) -> Any: ...
def f2(value: Any, values: Dict[str, Any]) -> Any: ...

class Model(BaseModel):
    x: int

    @validator('x')
    @classmethod  # optional
    def val_x1(cls, value: Any) -> Any: ...

    @validator('x')
    @classmethod  # optional
    def val_x2(cls, value: Any, values: Dict[str, Any]) -> Any: ...

    @validator('x')
    @staticmethod  # required
    def val_x3(value: Any) -> Any: ...

    @validator('x')
    @staticmethod  # required
    def val_x4(value: Any, values: Dict[str, Any]) -> Any: ...

    val_x5 = validator('x')(f1)
    val_x6 = validator('x')(f2)
"""


def make_generic_v1_field_validator(validator: V1Validator) -> FieldValidatorFunction:
    sig = signature(unwrap_unbound_methods(validator))
    positional_params: list[str] = []
    keyword_only_params: list[str] = []
    accepts_kwargs = False
    for param_name, parameter in sig.parameters.items():
        if param_name in ('field', 'config'):
            raise TypeError(
                'The `field` and `config` parameters are not available in Pydantic V2.'
                ' Please use the `info` parameter instead.'
                ' You can access the configuration via `info.config`,'
                ' but it is a dictionary instead of an object like it was in Pydantic V1.'
                ' The `field` argument is no longer available.'
            )
        if parameter.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD):
            positional_params.append(param_name)
        elif parameter.kind is Parameter.KEYWORD_ONLY:
            keyword_only_params.append(param_name)
        elif parameter.kind is Parameter.VAR_KEYWORD:
            accepts_kwargs = True

    accepts_values_kw = (keyword_only_params == ['values'] and len(positional_params) == 1) or (
        len(positional_params) == 2 and positional_params[1] == 'values'
    )

    if accepts_kwargs and len(positional_params) == 1:
        # has (v, **kwargs) or (v, values, **kwargs)
        val1 = cast(Union[V1ValidatorWithKwargs, V1ValidatorWithValuesAndKwargs], validator)

        def wrapper1(value: Any, info: FieldValidationInfo) -> Any:
            return val1(value, values=info.data)

        return wrapper1
    if len(positional_params) == 1 and keyword_only_params == []:
        # (v) -> Any
        val2 = cast(OnlyValueValidator, validator)

        def wrapper2(value: Any, _: ValidationInfo) -> Any:
            return val2(value)

        return wrapper2
    elif len(positional_params) in (1, 2) and accepts_values_kw:
        # (v, values) -> Any or (v, *, values) -> Any
        val3 = cast(V1ValidatorWithValues, validator)

        def wrapper3(value: Any, info: FieldValidationInfo) -> Any:
            return val3(value, values=info.data)

        return wrapper3
    raise TypeError(
        f'Unsupported signature for V1 style validator {validator}: {sig} is not supported.'
        f' Valid signatures are:\n{V1_VALIDATOR_VALID_SIGNATURES}'
    )


@overload
def make_generic_v2_field_validator(
    validator: FieldWrapValidatorFunction, mode: Literal['wrap']
) -> FieldWrapValidatorFunction:
    ...


@overload
def make_generic_v2_field_validator(
    validator: OnlyValueValidator | FieldValidatorFunction, mode: Literal['before', 'after', 'plain']
) -> FieldValidatorFunction:
    ...


def make_generic_v2_field_validator(
    validator: OnlyValueValidator | FieldValidatorFunction | FieldWrapValidatorFunction, mode: str
) -> FieldValidatorFunction | FieldWrapValidatorFunction:
    """
    In order to support different signatures, including deprecated validator signatures from v1,
    we introspect the function signature and wrap it in a parent function that has a signature
    compatible with pydantic_core
    """
    if mode in ('before', 'after', 'plain') and len(signature(validator).parameters) == 1:
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
