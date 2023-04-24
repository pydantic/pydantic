"""
Public methods used as decorators within pydantic models and dataclasses.
"""

from __future__ import annotations as _annotations

from functools import partial, partialmethod
from types import FunctionType
from typing import TYPE_CHECKING, Any, Callable, TypeVar, Union, overload
from warnings import warn

from pydantic_core import core_schema as _core_schema
from typing_extensions import Literal, Protocol, TypeAlias

from ._internal import _decorators, _decorators_v1
from .errors import PydanticUserError

_ALLOW_REUSE_WARNING_MESSAGE = '`allow_reuse` is deprecated and will be ignored; it should no longer be necessary'


if TYPE_CHECKING:

    class _OnlyValueValidatorClsMethod(Protocol):
        def __call__(self, __cls: Any, __value: Any) -> Any:
            ...

    class _V1ValidatorWithValuesClsMethod(Protocol):
        def __call__(self, __cls: Any, __value: Any, values: dict[str, Any]) -> Any:
            ...

    class _V1ValidatorWithValuesKwOnlyClsMethod(Protocol):
        def __call__(self, __cls: Any, __value: Any, *, values: dict[str, Any]) -> Any:
            ...

    class _V1ValidatorWithKwargsClsMethod(Protocol):
        def __call__(self, __cls: Any, **kwargs: Any) -> Any:
            ...

    class _V1ValidatorWithValuesAndKwargsClsMethod(Protocol):
        def __call__(self, __cls: Any, values: dict[str, Any], **kwargs: Any) -> Any:
            ...

    class _V2ValidatorClsMethod(Protocol):
        def __call__(self, __cls: Any, __input_value: Any, __info: _core_schema.FieldValidationInfo) -> Any:
            ...

    class _V2WrapValidatorClsMethod(Protocol):
        def __call__(
            self,
            __cls: Any,
            __input_value: Any,
            __validator: _core_schema.ValidatorFunctionWrapHandler,
            __info: _core_schema.ValidationInfo,
        ) -> Any:
            ...

    class _V1RootValidatorClsMethod(Protocol):
        def __call__(
            self, __cls: Any, __values: _decorators_v1.RootValidatorValues
        ) -> _decorators_v1.RootValidatorValues:
            ...

    V1Validator = Union[
        _OnlyValueValidatorClsMethod,
        _V1ValidatorWithValuesClsMethod,
        _V1ValidatorWithValuesKwOnlyClsMethod,
        _V1ValidatorWithKwargsClsMethod,
        _V1ValidatorWithValuesAndKwargsClsMethod,
        _decorators_v1.V1ValidatorWithValues,
        _decorators_v1.V1ValidatorWithValuesKwOnly,
        _decorators_v1.V1ValidatorWithKwargs,
        _decorators_v1.V1ValidatorWithValuesAndKwargs,
    ]

    V2Validator = Union[
        _V2ValidatorClsMethod,
        _core_schema.FieldValidatorFunction,
        _OnlyValueValidatorClsMethod,
        _core_schema.NoInfoValidatorFunction,
    ]

    V2WrapValidator = Union[
        _V2WrapValidatorClsMethod,
        _core_schema.GeneralWrapValidatorFunction,
        _core_schema.FieldWrapValidatorFunction,
    ]

    V1RootValidator = Union[
        _V1RootValidatorClsMethod,
        _decorators_v1.V1RootValidatorFunction,
    ]

    _PartialClsOrStaticMethod: TypeAlias = Union[classmethod[Any, Any, Any], staticmethod[Any, Any], partialmethod[Any]]

    # Allow both a V1 (assumed pre=False) or V2 (assumed mode='after') validator
    # We lie to type checkers and say we return the same thing we get
    # but in reality we return a proxy object that _mostly_ behaves like the wrapped thing
    _V1ValidatorType = TypeVar('_V1ValidatorType', V1Validator, _PartialClsOrStaticMethod)
    _V2BeforeAfterOrPlainValidatorType = TypeVar(
        '_V2BeforeAfterOrPlainValidatorType',
        V2Validator,
        _PartialClsOrStaticMethod,
    )
    _V2WrapValidatorType = TypeVar('_V2WrapValidatorType', V2WrapValidator, _PartialClsOrStaticMethod)
    _V1RootValidatorFunctionType = TypeVar(
        '_V1RootValidatorFunctionType',
        _decorators_v1.V1RootValidatorFunction,
        _V1RootValidatorClsMethod,
        _PartialClsOrStaticMethod,
    )


def validator(
    __field: str,
    *fields: str,
    pre: bool = False,
    each_item: bool = False,
    always: bool = False,
    check_fields: bool | None = None,
    allow_reuse: bool = False,
) -> Callable[[_V1ValidatorType], _V1ValidatorType]:
    """
    Decorate methods on the class indicating that they should be used to validate fields.

    Args:
        __field (str): The first field the validator should be called on; this is separate
            from `fields` to ensure an error is raised if you don't pass at least one.
        *fields (str): Additional field(s) the validator should be called on.
        pre (bool, optional): Whether or not this validator should be called before the standard
            validators (else after). Defaults to False.
        each_item (bool, optional): For complex objects (sets, lists etc.) whether to validate
            individual elements rather than the whole object. Defaults to False.
        always (bool, optional): Whether this method and other validators should be called even if
            the value is missing. Defaults to False.
        check_fields (bool | None, optional): Whether to check that the fields actually exist on the model.
            Defaults to None.
        allow_reuse (bool, optional): Whether to track and raise an error if another validator refers to
            the decorated function. Defaults to False.

    Returns:
        Callable: A decorator that can be used to decorate a
            function to be used as a validator.
    """
    if allow_reuse is True:  # pragma: no cover
        warn(_ALLOW_REUSE_WARNING_MESSAGE, DeprecationWarning)
    fields = tuple((__field, *fields))
    if isinstance(fields[0], FunctionType):
        raise PydanticUserError(
            "validators should be used with fields and keyword arguments, not bare. "
            "E.g. usage should be `@validator('<field_name>', ...)`",
            code='validator-no-fields',
        )
    elif not all(isinstance(field, str) for field in fields):
        raise PydanticUserError(
            "validator fields should be passed as separate string args. "
            "E.g. usage should be `@validator('<field_name_1>', '<field_name_2>', ...)`",
            code='validator-invalid-fields',
        )

    warn(
        'Pydantic V1 style `@validator` validators are deprecated.'
        ' You should migrate to Pydantic V2 style `@field_validator` validators,'
        ' see the migration guide for more details',
        DeprecationWarning,
        stacklevel=2,
    )

    mode: Literal['before', 'after'] = 'before' if pre is True else 'after'

    def dec(f: Any) -> _decorators.PydanticDescriptorProxy[Any]:
        if _decorators.is_instance_method_from_sig(f):
            raise PydanticUserError(
                '`@validator` cannot be applied to instance methods', code='validator-instance-method'
            )
        # auto apply the @classmethod decorator
        f = _decorators.ensure_classmethod_based_on_signature(f)
        wrap = _decorators_v1.make_generic_v1_field_validator
        validator_wrapper_info = _decorators.ValidatorDecoratorInfo(
            fields=fields,
            mode=mode,
            each_item=each_item,
            always=always,
            check_fields=check_fields,
        )
        return _decorators.PydanticDescriptorProxy(f, validator_wrapper_info, shim=wrap)

    return dec  # type: ignore[return-value]


@overload
def field_validator(
    __field: str,
    *fields: str,
    mode: Literal['before', 'after', 'plain'] = ...,
    check_fields: bool | None = ...,
) -> Callable[[_V2BeforeAfterOrPlainValidatorType], _V2BeforeAfterOrPlainValidatorType]:
    ...


@overload
def field_validator(
    __field: str,
    *fields: str,
    mode: Literal['wrap'],
    check_fields: bool | None = ...,
) -> Callable[[_V2WrapValidatorType], _V2WrapValidatorType]:
    ...


FieldValidatorModes: TypeAlias = Literal['before', 'after', 'wrap', 'plain']


def field_validator(
    __field: str,
    *fields: str,
    mode: FieldValidatorModes = 'after',
    check_fields: bool | None = None,
) -> Callable[[Any], Any]:
    """
    Decorate methods on the class indicating that they should be used to validate fields.

    Args:
        __field (str): The first field the field_validator should be called on; this is separate
            from `fields` to ensure an error is raised if you don't pass at least one.
        *fields (tuple): Additional field(s) the field_validator should be called on.
        mode (FieldValidatorModes): Specifies whether to validate the fields before or after validation.
             Defaults to 'after'.
        check_fields (bool | None): If set to True, checks that the fields actually exist on the model.
            Defaults to None.

    Returns:
        Callable: A decorator that can be used to decorate a function to be used as a field_validator.
    """
    if isinstance(__field, FunctionType):
        raise PydanticUserError(
            'field_validators should be used with fields and keyword arguments, not bare. '
            "E.g. usage should be `@validator('<field_name>', ...)`",
            code='validator-no-fields',
        )
    fields = __field, *fields
    if not all(isinstance(field, str) for field in fields):
        raise PydanticUserError(
            'field_validator fields should be passed as separate string args. '
            "E.g. usage should be `@validator('<field_name_1>', '<field_name_2>', ...)`",
            code='validator-invalid-fields',
        )

    def dec(
        f: Callable[..., Any] | staticmethod[Any, Any] | classmethod[Any, Any, Any]
    ) -> _decorators.PydanticDescriptorProxy[Any]:
        if _decorators.is_instance_method_from_sig(f):
            raise PydanticUserError(
                '`@field_validator` cannot be applied to instance methods', code='validator-instance-method'
            )

        # auto apply the @classmethod decorator
        f = _decorators.ensure_classmethod_based_on_signature(f)

        dec_info = _decorators.FieldValidatorDecoratorInfo(fields=fields, mode=mode, check_fields=check_fields)
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    return dec


@overload
def root_validator(
    *,
    # if you don't specify `pre` the default is `pre=False`
    # which means you need to specify `skip_on_failure=True`
    skip_on_failure: Literal[True],
    allow_reuse: bool = ...,
) -> Callable[[_V1RootValidatorFunctionType], _V1RootValidatorFunctionType,]:
    ...


@overload
def root_validator(
    *,
    # if you specify `pre=True` then you don't need to specify
    # `skip_on_failure`, in fact it is not allowed as an argument!
    pre: Literal[True],
    allow_reuse: bool = ...,
) -> Callable[[_V1RootValidatorFunctionType], _V1RootValidatorFunctionType,]:
    ...


@overload
def root_validator(
    *,
    # if you explicitly specify `pre=False` then you
    # MUST specify `skip_on_failure=True`
    pre: Literal[False],
    skip_on_failure: Literal[True],
    allow_reuse: bool = ...,
) -> Callable[[_V1RootValidatorFunctionType], _V1RootValidatorFunctionType,]:
    ...


def root_validator(
    *,
    pre: bool = False,
    skip_on_failure: bool = False,
    allow_reuse: bool = False,
) -> Any:
    """
    Decorate methods on a model indicating that they should be used to validate (and perhaps
    modify) data either before or after standard model parsing/validation is performed.

    Args:
        pre (bool, optional): Whether or not this validator should be called before the standard
            validators (else after). Defaults to False.
        skip_on_failure (bool, optional): Whether to stop validation and return as soon as a
            failure is encountered. Defaults to False.
        allow_reuse (bool, optional): Whether to track and raise an error if another validator
            refers to the decorated function. Defaults to False.

    Returns:
        Any: A decorator that can be used to decorate a function to be used as a root_validator.
    """
    if allow_reuse is True:  # pragma: no cover
        warn(_ALLOW_REUSE_WARNING_MESSAGE, DeprecationWarning)
    mode: Literal['before', 'after'] = 'before' if pre is True else 'after'
    if pre is False and skip_on_failure is not True:
        raise PydanticUserError(
            'If you use `@root_validator` with pre=False (the default) you MUST specify `skip_on_failure=True`.',
            code='root-validator-pre-skip',
        )

    wrap = partial(_decorators_v1.make_v1_generic_root_validator, pre=pre)

    def dec(f: Callable[..., Any] | classmethod[Any, Any, Any] | staticmethod[Any, Any]) -> Any:
        if _decorators.is_instance_method_from_sig(f):
            raise TypeError('`@root_validator` cannot be applied to instance methods')
        # auto apply the @classmethod decorator
        res = _decorators.ensure_classmethod_based_on_signature(f)
        dec_info = _decorators.RootValidatorDecoratorInfo(mode=mode)
        return _decorators.PydanticDescriptorProxy(res, dec_info, shim=wrap)

    return dec


if TYPE_CHECKING:
    _PlainSerializationFunction = Union[_core_schema.SerializerFunction, _PartialClsOrStaticMethod]

    _WrapSerializationFunction = Union[_core_schema.WrapSerializerFunction, _PartialClsOrStaticMethod]

    _PlainSerializeMethodType = TypeVar('_PlainSerializeMethodType', bound=_PlainSerializationFunction)
    _WrapSerializeMethodType = TypeVar('_WrapSerializeMethodType', bound=_WrapSerializationFunction)


@overload
def field_serializer(
    __field: str,
    *fields: str,
    json_return_type: _core_schema.JsonReturnTypes | None = ...,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = ...,
    check_fields: bool | None = ...,
) -> Callable[[_PlainSerializeMethodType], _PlainSerializeMethodType]:
    ...


@overload
def field_serializer(
    __field: str,
    *fields: str,
    mode: Literal['plain'],
    json_return_type: _core_schema.JsonReturnTypes | None = ...,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = ...,
    check_fields: bool | None = ...,
) -> Callable[[_PlainSerializeMethodType], _PlainSerializeMethodType]:
    ...


@overload
def field_serializer(
    __field: str,
    *fields: str,
    mode: Literal['wrap'],
    json_return_type: _core_schema.JsonReturnTypes | None = ...,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = ...,
    check_fields: bool | None = ...,
) -> Callable[[_WrapSerializeMethodType], _WrapSerializeMethodType]:
    ...


def field_serializer(
    *fields: str,
    mode: Literal['plain', 'wrap'] = 'plain',
    json_return_type: _core_schema.JsonReturnTypes | None = None,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always',
    check_fields: bool | None = None,
) -> Callable[[Any], Any]:
    """
    Decorate methods on the class indicating that they should be used to serialize fields.

    Four signatures are supported:

    - `(self, value: Any, info: FieldSerializationInfo)`
    - `(self, value: Any, nxt: SerializerFunctionWrapHandler, info: FieldSerializationInfo)`
    - `(value: Any, info: SerializationInfo)`
    - `(value: Any, nxt: SerializerFunctionWrapHandler, info: SerializationInfo)`

    Args:
        fields (str): Which field(s) the method should be called on.
        mode (str): `plain` means the function will be called instead of the default serialization logic,
            `wrap` means the function will be called with an argument to optionally call the
            default serialization logic.
        json_return_type (str): The type that the function returns if the serialization mode is JSON.
        when_used (str): When the function should be called.
        check_fields (bool): Whether to check that the fields actually exist on the model.

    Returns:
        Callable: A decorator that can be used to decorate a function to be used as a field serializer.
    """

    def dec(
        f: Callable[..., Any] | staticmethod[Any, Any] | classmethod[Any, Any, Any]
    ) -> _decorators.PydanticDescriptorProxy[Any]:
        dec_info = _decorators.FieldSerializerDecoratorInfo(
            fields=fields,
            mode=mode,
            json_return_type=json_return_type,
            when_used=when_used,
            check_fields=check_fields,
        )
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    return dec


def model_serializer(
    __f: Callable[..., Any] | None = None,
    *,
    mode: Literal['plain', 'wrap'] = 'plain',
    json_return_type: _core_schema.JsonReturnTypes | None = None,
) -> Callable[[Any], _decorators.PydanticDescriptorProxy[Any]] | _decorators.PydanticDescriptorProxy[Any]:
    """
    Decorate a function which will be called to serialize the model.

    (`when_used` is not permitted here since it makes no sense.)

    Args:
        __f (Callable[..., Any] | None): The function to be decorated.
        mode (Literal['plain', 'wrap']): The serialization mode. `'plain'` means the function will be called
            instead of the default serialization logic, `'wrap'` means the function will be called with an argument
            to optionally call the default serialization logic.
        json_return_type (_core_schema.JsonReturnTypes | None): The type that the function returns if the
            serialization mode is JSON.

    Returns:
        Callable: A decorator that can be used to decorate a function to be used as a model serializer.
    """

    def dec(f: Callable[..., Any]) -> _decorators.PydanticDescriptorProxy[Any]:
        dec_info = _decorators.ModelSerializerDecoratorInfo(mode=mode, json_return_type=json_return_type)
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    if __f is None:
        return dec
    else:
        return dec(__f)


ModelType = TypeVar('ModelType')
ModelWrapValidatorHandler = Callable[[Any], ModelType]


class ModelWrapValidatorWithoutInfo(Protocol):
    def __call__(
        self,
        cls: type[ModelType],
        # this can be a dict, a model instance
        # or anything else that gets passed to validate_python
        # thus validators _must_ handle all cases
        __value: Any,
        __handler: Callable[[Any], ModelType],
    ) -> ModelType:
        ...


class ModelWrapValidator(Protocol):
    def __call__(
        self,
        cls: type[ModelType],
        # this can be a dict, a model instance
        # or anything else that gets passed to validate_python
        # thus validators _must_ handle all cases
        __value: Any,
        __handler: Callable[[Any], ModelType],
        __info: _core_schema.ValidationInfo,
    ) -> ModelType:
        ...


class ModelBeforeValidatorWithoutInfo(Protocol):
    def __call__(
        self,
        cls: Any,
        # this can be a dict, a model instance
        # or anything else that gets passed to validate_python
        # thus validators _must_ handle all cases
        __value: Any,
    ) -> Any:
        ...


class ModelBeforeValidator(Protocol):
    def __call__(
        self,
        cls: Any,
        # this can be a dict, a model instance
        # or anything else that gets passed to validate_python
        # thus validators _must_ handle all cases
        __value: Any,
        __info: _core_schema.ValidationInfo,
    ) -> Any:
        ...


class ModelAfterValidatorWithoutInfo(Protocol):
    @staticmethod
    def __call__(
        self: ModelType,  # type: ignore
    ) -> ModelType:
        ...


class ModelAfterValidator(Protocol):
    @staticmethod
    def __call__(
        self: ModelType,  # type: ignore
        __info: _core_schema.ValidationInfo,
    ) -> ModelType:
        ...


AnyModelWrapValidator = Union[ModelWrapValidator, ModelWrapValidatorWithoutInfo]
AnyModeBeforeValidator = Union[ModelBeforeValidator, ModelBeforeValidatorWithoutInfo]
AnyModeAfterValidator = Union[ModelAfterValidator, ModelAfterValidatorWithoutInfo]


@overload
def model_validator(
    *,
    mode: Literal['wrap'],
) -> Callable[[AnyModelWrapValidator], _decorators.PydanticDescriptorProxy[_decorators.ModelValidatorDecoratorInfo]]:
    ...


@overload
def model_validator(
    *,
    mode: Literal['before'],
) -> Callable[[AnyModeBeforeValidator], _decorators.PydanticDescriptorProxy[_decorators.ModelValidatorDecoratorInfo]]:
    ...


@overload
def model_validator(
    *,
    mode: Literal['after'],
) -> Callable[[AnyModeAfterValidator], _decorators.PydanticDescriptorProxy[_decorators.ModelValidatorDecoratorInfo]]:
    ...


def model_validator(
    *,
    mode: Literal['wrap', 'before', 'after'],
) -> Any:
    """
    Decorate model methods for validation purposes.

    Args:
        mode (Literal['wrap', 'before', 'after']): A required string literal that specifies the validation mode.
            It can be one of the following: 'wrap', 'before', or 'after'.

    Returns:
        Any: A decorator that can be used to decorate a function to be used as a model validator.
    """

    def dec(f: Any) -> _decorators.PydanticDescriptorProxy[Any]:
        # auto apply the @classmethod decorator
        f = _decorators.ensure_classmethod_based_on_signature(f)
        dec_info = _decorators.ModelValidatorDecoratorInfo(mode=mode)
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    return dec
