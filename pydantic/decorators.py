"""
Public methods related to:
* `validator` - a decorator to add validation to a field on a model
* `root_validator` - a decorator to add validation to a model as a whole
* `serializer` - a decorator to add serialization to a field on a model
"""

from __future__ import annotations as _annotations

from functools import partial
from types import FunctionType
from typing import Any, Callable, TypeVar, Union, overload
from warnings import warn

from pydantic_core import core_schema as _core_schema
from typing_extensions import Literal, Protocol

from ._internal import _decorators


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
    def __call__(self, __cls: Any, __values: _decorators.RootValidatorValues) -> _decorators.RootValidatorValues:
        ...


V1Validator = Union[
    _OnlyValueValidatorClsMethod,
    _V1ValidatorWithValuesClsMethod,
    _V1ValidatorWithValuesKwOnlyClsMethod,
    _V1ValidatorWithKwargsClsMethod,
    _V1ValidatorWithValuesAndKwargsClsMethod,
    _decorators.V1ValidatorWithValues,
    _decorators.V1ValidatorWithValuesKwOnly,
    _decorators.V1ValidatorWithKwargs,
    _decorators.V1ValidatorWithValuesAndKwargs,
]

V2Validator = Union[
    _V2ValidatorClsMethod,
    _core_schema.FieldValidatorFunction,
    _OnlyValueValidatorClsMethod,
    _decorators.OnlyValueValidator,
]

V2WrapValidator = Union[
    _V2WrapValidatorClsMethod,
    _core_schema.GeneralWrapValidatorFunction,
    _core_schema.FieldWrapValidatorFunction,
]

V1RootValidator = Union[
    _V1RootValidatorClsMethod,
    _decorators.V1RootValidatorFunction,
]


# Allow both a V1 (assumed pre=False) or V2 (assumed mode='after') validator
# We lie to type checkers and say we return the same thing we get
# but in reality we return a proxy object that _mostly_ behaves like the wrapped thing
_V1ValidatorType = TypeVar('_V1ValidatorType', bound=Union[V1Validator, 'classmethod[Any]', 'staticmethod[Any]'])
_V2BeforeAfterOrPlainValidatorType = TypeVar(
    '_V2BeforeAfterOrPlainValidatorType',
    bound=Union[V2Validator, 'classmethod[Any]', 'staticmethod[Any]'],
)
_V2WrapValidatorType = TypeVar(
    '_V2WrapValidatorType', bound=Union[V2WrapValidator, 'classmethod[Any]', 'staticmethod[Any]']
)
_V1RootValidatorFunctionType = TypeVar(
    '_V1RootValidatorFunctionType',
    bound=Union[
        _decorators.V1RootValidatorFunction,
        _V1RootValidatorClsMethod,
        'classmethod[Any]',
        'staticmethod[Any]',
    ],
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
    Decorate methods on the class indicating that they should be used to validate fields
    :param __field: the first field the validator should be called on;
        this is separate from `fields` to ensure an error is raised if you don't pass at least one
    :param fields: additional field(s) the validator should be called on
    :param pre: whether or not this validator should be called before the standard validators (else after)
    :param each_item: for complex objects (sets, lists etc.) whether to validate individual elements rather than the
      whole object
    :param always: whether this method and other validators should be called even if the value is missing
    :param check_fields: whether to check that the fields actually exist on the model
    :param allow_reuse: whether to track and raise an error if another validator refers to the decorated function
    """
    fields = tuple((__field, *fields))
    if isinstance(fields[0], FunctionType):
        raise TypeError(
            'field_validators should be used with fields and keyword arguments, not bare. '
            "E.g. usage should be `@validator('<field_name>', ...)`"
        )
    elif not all(isinstance(field, str) for field in fields):
        raise TypeError(
            'validator fields should be passed as separate string args. '
            "E.g. usage should be `@validator('<field_name_1>', '<field_name_2>', ...)`"
        )

    warn(
        'Pydantic V1 style `@validator` validators are deprecated.'
        ' You should migrate to Pydantic V2 style `@field_validator` validators,'
        ' see the migration guide for more details',
        DeprecationWarning,
        stacklevel=2,
    )

    mode: Literal['before', 'after'] = 'before' if pre is True else 'after'

    def dec(f: Any) -> _decorators.PydanticDecoratorMarker[Any]:
        if _decorators.is_instance_method_from_sig(f):
            raise TypeError('`@validator` cannot be applied to instance methods')
        _decorators.check_for_duplicate_validator(f, allow_reuse=allow_reuse)
        # auto apply the @classmethod decorator
        f = _decorators.ensure_classmethod_based_on_signature(f)
        wrap = _decorators.make_generic_v1_field_validator
        validator_wrapper_info = _decorators.ValidatorDecoratorInfo(
            fields=fields,
            mode=mode,
            each_item=each_item,
            always=always,
            check_fields=check_fields,
        )
        return _decorators.PydanticDecoratorMarker(f, validator_wrapper_info, shim=wrap)

    return dec  # type: ignore[return-value]


@overload
def field_validator(
    __field: str,
    *fields: str,
    mode: Literal['before', 'after', 'plain'] = ...,
    check_fields: bool | None = ...,
    sub_path: tuple[str | int, ...] | None = ...,
    allow_reuse: bool = False,
) -> Callable[[_V2BeforeAfterOrPlainValidatorType], _V2BeforeAfterOrPlainValidatorType]:
    ...


@overload
def field_validator(
    __field: str,
    *fields: str,
    mode: Literal['wrap'],
    check_fields: bool | None = ...,
    sub_path: tuple[str | int, ...] | None = ...,
    allow_reuse: bool = False,
) -> Callable[[_V2WrapValidatorType], _V2WrapValidatorType]:
    ...


def field_validator(
    __field: str,
    *fields: str,
    mode: Literal['before', 'after', 'wrap', 'plain'] = 'after',
    check_fields: bool | None = None,
    sub_path: tuple[str | int, ...] | None = None,
    allow_reuse: bool = False,
) -> Callable[[Any], Any]:
    """
    Decorate methods on the class indicating that they should be used to validate fields
    :param __field: the first field the field_validator should be called on;
        this is separate from `fields` to ensure an error is raised if you don't pass at least one
    :param fields: additional field(s) the field_validator should be called on
    :param mode: TODO
    :param check_fields: whether to check that the fields actually exist on the model
    :param sub_path: TODO
    :param allow_reuse: whether to track and raise an error if another validator refers to the decorated function
    """
    fields = tuple((__field, *fields))
    if isinstance(fields[0], FunctionType):
        raise TypeError(
            'field_validators should be used with fields and keyword arguments, not bare. '
            "E.g. usage should be `@validator('<field_name>', ...)`"
        )
    elif not all(isinstance(field, str) for field in fields):
        raise TypeError(
            'field_validator fields should be passed as separate string args. '
            "E.g. usage should be `@validator('<field_name_1>', '<field_name_2>', ...)`"
        )

    def dec(f: Callable[..., Any] | staticmethod[Any] | classmethod[Any]) -> _decorators.PydanticDecoratorMarker[Any]:
        if _decorators.is_instance_method_from_sig(f):
            raise TypeError('`@field_validator` cannot be applied to instance methods')
        _decorators.check_for_duplicate_validator(f, allow_reuse=allow_reuse)
        # auto apply the @classmethod decorator and warn users if we had to do so
        f = _decorators.ensure_classmethod_based_on_signature(f)

        wrap = partial(_decorators.make_generic_v2_field_validator, mode=mode)

        validator_wrapper_info = _decorators.FieldValidatorDecoratorInfo(
            fields=fields, mode=mode, sub_path=sub_path, check_fields=check_fields
        )
        return _decorators.PydanticDecoratorMarker(f, validator_wrapper_info, shim=wrap)

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
) -> Callable[[Any], _decorators.PydanticDecoratorMarker[Any]]:
    """
    Decorate methods on a model indicating that they should be used to validate (and perhaps modify) data either
    before or after standard model parsing/validation is performed.
    """
    mode: Literal['before', 'after'] = 'before' if pre is True else 'after'
    if pre is False and skip_on_failure is not True:
        raise TypeError(
            'If you use `@root_validator` with pre=False (the default)'
            ' you MUST specify `skip_on_failure=True`.'
            ' The `skip_on_failure=False` option is no longer available.'
            ' If you were not trying to set `skip_on_failure=False` you'
            ' can safely set `skip_on_failure=True`.'
            ' If you do, this root validator will no longer be called'
            ' if validation fails for any of the fields.'
            ' Please see the migration guide for more details.'
        )
    wrap = partial(_decorators.make_v1_generic_root_validator, pre=pre)

    def dec(f: Callable[..., Any] | classmethod[Any] | staticmethod[Any]) -> Any:
        if _decorators.is_instance_method_from_sig(f):
            raise TypeError('`@root_validator` cannot be applied to instance methods')
        _decorators.check_for_duplicate_validator(f, allow_reuse=allow_reuse)
        # auto apply the @classmethod decorator and warn users if we had to do so
        res = _decorators.ensure_classmethod_based_on_signature(f)
        validator_wrapper_info = _decorators.RootValidatorDecoratorInfo(mode=mode)
        return _decorators.PydanticDecoratorMarker(res, validator_wrapper_info, shim=wrap)

    return dec


_PlainSerializationFunction = Union[
    _core_schema.GeneralPlainSerializerFunction,
    _core_schema.FieldPlainSerializerFunction,
    _decorators.GenericPlainSerializerFunctionWithoutInfo,
    _decorators.FieldPlainSerializerFunctionWithoutInfo,
]


_WrapSerializationFunction = Union[
    _core_schema.GeneralWrapSerializerFunction,
    _core_schema.FieldWrapSerializerFunction,
    _decorators.GeneralWrapSerializerFunctionWithoutInfo,
    _decorators.FieldWrapSerializerFunctionWithoutInfo,
]


_PlainSerializeMethodType = TypeVar('_PlainSerializeMethodType', bound=_PlainSerializationFunction)
_WrapSerializeMethodType = TypeVar('_WrapSerializeMethodType', bound=_WrapSerializationFunction)


@overload
def field_serializer(
    __field: str,
    *fields: str,
    json_return_type: _core_schema.JsonReturnTypes | None = ...,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = ...,
    sub_path: tuple[str | int, ...] | None = ...,
    check_fields: bool | None = ...,
    allow_reuse: bool = ...,
) -> Callable[[_PlainSerializeMethodType], _PlainSerializeMethodType]:
    ...


@overload
def field_serializer(
    __field: str,
    *fields: str,
    mode: Literal['plain'],
    json_return_type: _core_schema.JsonReturnTypes | None = ...,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = ...,
    sub_path: tuple[str | int, ...] | None = ...,
    check_fields: bool | None = ...,
    allow_reuse: bool = ...,
) -> Callable[[_PlainSerializeMethodType], _PlainSerializeMethodType]:
    ...


@overload
def field_serializer(
    __field: str,
    *fields: str,
    mode: Literal['wrap'],
    json_return_type: _core_schema.JsonReturnTypes | None = ...,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = ...,
    sub_path: tuple[str | int, ...] | None = ...,
    check_fields: bool | None = ...,
    allow_reuse: bool = ...,
) -> Callable[[_WrapSerializeMethodType], _WrapSerializeMethodType]:
    ...


def field_serializer(
    *fields: str,
    mode: Literal['plain', 'wrap'] = 'plain',
    json_return_type: _core_schema.JsonReturnTypes | None = None,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always',
    sub_path: tuple[str | int, ...] | None = None,
    check_fields: bool | None = None,
    allow_reuse: bool = False,
) -> Callable[[Any], Any]:
    """
    Decorate methods on the class indicating that they should be used to serialize fields.
    Four signatures are supported:
    - (self, value: Any, info: FieldSerializationInfo)
    - (self, value: Any, nxt: SerializerFunctionWrapHandler, info: FieldSerializationInfo)
    - (value: Any, info: SerializationInfo)
    - (value: Any, nxt: SerializerFunctionWrapHandler, info: SerializationInfo)

    :param fields: which field(s) the method should be called on
    :param mode: `'plain'` means the function will be called instead of the default serialization logic,
        `'wrap'` means the function will be called with an argument to optionally call the default serialization logic.
    :param json_return_type: The type that the function returns if the serialization mode is JSON.
    :param when_used: When the function should be called
    :param sub_path: TODO
    :param check_fields: whether to check that the fields actually exist on the model
    :param allow_reuse: whether to track and raise an error if another validator refers to the decorated function
    """

    def dec(f: Callable[..., Any] | staticmethod[Any] | classmethod[Any]) -> _decorators.PydanticDecoratorMarker[Any]:
        res = _decorators.prepare_serializer_decorator(f, allow_reuse)
        type_: Literal['field', 'general'] = 'field' if _decorators.is_instance_method_from_sig(f) else 'general'

        dec_info = _decorators.FieldSerializerDecoratorInfo(
            fields=fields,
            mode=mode,
            type=type_,
            json_return_type=json_return_type,
            when_used=when_used,
            sub_path=sub_path,
            check_fields=check_fields,
        )
        return _decorators.PydanticDecoratorMarker(
            res, dec_info, shim=partial(_decorators.make_generic_field_serializer, mode=mode, type=type_)
        )

    return dec


def model_serializer(
    __f: Callable[..., Any] = None,
    *,
    mode: Literal['plain', 'wrap'] = 'plain',
    json_return_type: _core_schema.JsonReturnTypes | None = None,
    allow_reuse: bool = False,
) -> Callable[[Any], _decorators.PydanticDecoratorMarker[Any]] | _decorators.PydanticDecoratorMarker[Any]:
    """
    Function decorate to add a function which will be called to serialize the model.

    (`when_used` is not permitted here since it make no sense)

    :param mode: `'plain'` means the function will be called instead of the default serialization logic,
        `'wrap'` means the function will be called with an argument to optionally call the default serialization logic.
    :param json_return_type: The type that the function returns if the serialization mode is JSON.
    :param allow_reuse: whether to track and raise an error if another validator refers to the decorated function
    """

    def dec(f: Callable[..., Any]) -> _decorators.PydanticDecoratorMarker[Any]:
        if isinstance(f, (staticmethod, classmethod)) or not _decorators.is_instance_method_from_sig(f):
            raise TypeError('`@model_serializer` must be applied to instance methods')

        res = _decorators.prepare_serializer_decorator(f, allow_reuse)

        dec_info = _decorators.ModelSerializerDecoratorInfo(
            mode=mode,
            json_return_type=json_return_type,
        )
        return _decorators.PydanticDecoratorMarker(
            res, dec_info, shim=partial(_decorators.make_generic_model_serializer, mode=mode)
        )

    if __f is None:
        return dec
    else:
        return dec(__f)
