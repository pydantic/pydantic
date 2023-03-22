"""
Public methods related to:
* `validator` - a decorator to add validation to a field on a model
* `root_validator` - a decorator to add validation to a model as a whole
* `serializer` - a decorator to add serialization to a field on a model
"""

from __future__ import annotations as _annotations

from functools import partial
from typing import Any, Callable, TypeVar, Union, overload
from warnings import warn

from pydantic_core import core_schema as _core_schema
from typing_extensions import Literal, Protocol

from ._internal import _decorators
from .errors import PydanticUserError


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
_V2ValidatorType = TypeVar('_V2ValidatorType', bound=Union[V2Validator, 'classmethod[Any]', 'staticmethod[Any]'])
_V1OrV2ValidatorType = TypeVar(
    '_V1OrV2ValidatorType', bound=Union[V1Validator, V2Validator, 'classmethod[Any]', 'staticmethod[Any]']
)
_V2WrapValidatorType = TypeVar(
    '_V2WrapValidatorType', bound=Union[V2WrapValidator, 'classmethod[Any]', 'staticmethod[Any]']
)
_V1RootValidatorFunctionType = TypeVar(
    '_V1RootValidatorFunctionType',
    bound=Union[
        _decorators.V1RootValidatorFunction, _V1RootValidatorClsMethod, 'classmethod[Any]', 'staticmethod[Any]'
    ],
)


@overload
def validator(
    __field: str,
    *fields: str,
    check_fields: bool | None = ...,
    sub_path: tuple[str | int, ...] | None = ...,
    allow_reuse: bool = False,
) -> Callable[[_V1OrV2ValidatorType], _V1OrV2ValidatorType]:
    ...


# Only allow V1 only validators if pre is specified
@overload
def validator(
    __field: str,
    *fields: str,
    pre: bool,
    check_fields: bool | None = ...,
    sub_path: tuple[str | int, ...] | None = ...,
    allow_reuse: bool = False,
) -> Callable[[_V1ValidatorType], _V1ValidatorType]:
    ...


# Only allow V2 validators if mode is specified
@overload
def validator(
    __field: str,
    *fields: str,
    mode: Literal['before', 'after', 'plain'],
    check_fields: bool | None = ...,
    sub_path: tuple[str | int, ...] | None = ...,
    allow_reuse: bool = False,
) -> Callable[[_V2ValidatorType], _V2ValidatorType]:
    ...


@overload
def validator(
    __field: str,
    *fields: str,
    mode: Literal['wrap'],
    check_fields: bool | None = ...,
    sub_path: tuple[str | int, ...] | None = ...,
    allow_reuse: bool = False,
) -> Callable[[_V2WrapValidatorType], _V2WrapValidatorType]:
    ...


def validator(
    *fields: str,
    pre: bool | None = None,
    mode: Literal['before', 'after', 'wrap', 'plain'] | None = None,
    check_fields: bool | None = None,
    sub_path: tuple[str | int, ...] | None = None,
    allow_reuse: bool = False,
) -> Callable[[Any], Any]:
    """
    Decorate methods on the class indicating that they should be used to validate fields
    :param fields: which field(s) the method should be called on
    :param mode: TODO
    :param sub_path: TODO
    :param check_fields: whether to check that the fields actually exist on the model
    :param allow_reuse: whether to track and raise an error if another validator refers to the decorated function
    """
    if pre is not None and mode is not None:
        raise TypeError('Combining `pre` and `mode` is not allowed')
    if not fields:
        raise PydanticUserError('validator with no fields specified')

    if pre is not None:
        warn(
            'Pydantic V1 style validators using `pre=True` or `pre=False` are deprecated.'
            " You should migrate to Pydantic V2 style decorators using `mode='before'` or `mode='after'`",
            DeprecationWarning,
            stacklevel=2,
        )

    def dec(f: Callable[..., Any] | staticmethod[Any] | classmethod[Any]) -> _decorators.PydanticDecoratorMarker[Any]:
        nonlocal pre, mode
        if _decorators.is_instance_method_from_sig(f):
            raise TypeError('`@validator` cannot be applied to instance methods')
        if pre is None and mode is None:
            # check if we got a V1 or V2 validator and set the default accordingly
            if _decorators.is_v1_validator(f):
                pre = True
            elif not isinstance(f, classmethod) and _decorators.is_classmethod_from_sig(f):
                mode = 'after'
            else:
                mode = 'after'
        _decorators.check_for_duplicate_validator(f, allow_reuse=allow_reuse)
        # auto apply the @classmethod decorator and warn users if we had to do so
        f = _decorators.ensure_classmethod_based_on_signature(f)
        if pre is not None:
            # V1 validator
            warn(
                'Validator signatures using the `values` keyword argument or `**kwargs` are no longer supported.'
                ' Please use `info: pydantic.FieldValidationInfo` as the second positional argument instead.'
                ' Then you can retrieve `values` from `info.data`.'
                ' This compatibility shim will be removed in a future minor release of Pydantic v2.X',
                DeprecationWarning,
                stacklevel=2,
            )
            wrap = partial(_decorators.make_generic_v1_field_validator)
            mode = 'before' if pre is True else 'after'
        else:
            # V2 validator
            wrap = partial(_decorators.make_generic_v2_field_validator, mode=mode)

        assert mode is not None

        validator_wrapper_info = _decorators.ValidatorDecoratorInfo(
            fields=fields, type='field', mode=mode, sub_path=sub_path, check_fields=check_fields
        )
        return _decorators.PydanticDecoratorMarker(f, validator_wrapper_info, shim=wrap)

    return dec


@overload
def root_validator(
    *,
    # if you don't specify `pre` the default is `pre=False`
    # which means you need to specify `skip_on_failure=True`
    skip_on_failure: Literal[True] = ...,
    allow_reuse: bool = ...,
) -> Callable[[_V1RootValidatorFunctionType], _V1RootValidatorFunctionType,]:
    ...


@overload
def root_validator(
    *,
    # for pre=False you don't need to specify `skip_on_failure`
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
    skip_on_failure: Literal[True] = ...,
    allow_reuse: bool = ...,
) -> Callable[[_V1RootValidatorFunctionType], _V1RootValidatorFunctionType,]:
    ...


def root_validator(  # type: ignore[misc]
    __func: _V1RootValidatorFunctionType | None = None,
    *,
    pre: bool = False,
    skip_on_failure: bool = False,
    allow_reuse: bool = False,
) -> (
    _decorators.PydanticDecoratorMarker[Any]
    | Callable[
        [_V1RootValidatorFunctionType],
        _decorators.PydanticDecoratorMarker[Any],
    ]
):
    """
    Decorate methods on a model indicating that they should be used to validate (and perhaps modify) data either
    before or after standard model parsing/validation is performed.
    """
    mode = 'before' if pre is True else 'after'
    if pre is False and skip_on_failure is not True:
        raise TypeError(
            'If you use `@root_validator` with pre=False (the default)'
            ' you MUST specify `skip_on_failure=True`.'
            'The `skip_on_failure=False` option is no longer available.'
        )
    wrap = partial(_decorators.make_v1_generic_root_validator, pre=pre)
    if __func is not None:
        if _decorators.is_instance_method_from_sig(__func):
            raise TypeError('`@root_validator` cannot be applied to instance methods')
        _decorators.check_for_duplicate_validator(__func, allow_reuse=allow_reuse)
        # auto apply the @classmethod decorator and warn users if we had to do so
        res = _decorators.ensure_classmethod_based_on_signature(__func)
        validator_wrapper_info = _decorators.RootValidatorDecoratorInfo(mode=mode)  # type: ignore[arg-type]
        return _decorators.PydanticDecoratorMarker(res, validator_wrapper_info, shim=wrap)  # type: ignore[return-value]

    def dec(f: Callable[..., Any] | classmethod[Any] | staticmethod[Any]) -> Any:
        if _decorators.is_instance_method_from_sig(f):
            raise TypeError('`@root_validator` cannot be applied to instance methods')
        _decorators.check_for_duplicate_validator(f, allow_reuse=allow_reuse)
        # auto apply the @classmethod decorator and warn users if we had to do so
        res = _decorators.ensure_classmethod_based_on_signature(f)
        validator_wrapper_info = _decorators.RootValidatorDecoratorInfo(mode=mode)  # type: ignore[arg-type]
        return _decorators.PydanticDecoratorMarker(res, validator_wrapper_info, shim=wrap)

    return dec  # type: ignore[return-value]


_PlainSerializationFunction = Union[
    _core_schema.GeneralPlainSerializerFunction,
    _core_schema.FieldPlainSerializerFunction,
]


_WrapSerializationFunction = Union[
    _core_schema.GeneralWrapSerializerFunction,
    _core_schema.FieldWrapSerializerFunction,
]


_PlainSerializeMethodType = TypeVar('_PlainSerializeMethodType', bound=_PlainSerializationFunction)
_WrapSerializeMethodType = TypeVar('_WrapSerializeMethodType', bound=_WrapSerializationFunction)


@overload
def serializer(
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
def serializer(
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
def serializer(
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


def serializer(
    *fields: str,
    mode: Literal['plain', 'wrap'] = 'plain',
    json_return_type: _core_schema.JsonReturnTypes | None = None,
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always',
    sub_path: tuple[str | int, ...] | None = None,
    check_fields: bool | None = None,
    allow_reuse: bool = False,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorate methods on the class indicating that they should be used to serialize fields.
    Four signatures are supported:
    - (self, value: Any, info: FieldSerializationInfo)
    - (self, value: Any, nxt: SerializerFunctionWrapHandler, info: FieldSerializationInfo)
    - (value: Any, info: SerializationInfo)
    - (value: Any, nxt: SerializerFunctionWrapHandler, info: SerializationInfo)

    :param fields: which field(s) the method should be called on
    :param mode: TODO
    :param json_return_type: The type that the function returns if the serialization mode is JSON.
    :param when_used: When the function should be called
    :param sub_path: TODO
    :param check_fields: whether to check that the fields actually exist on the model
    :param allow_reuse: whether to track and raise an error if another validator refers to the decorated function
    """

    def dec(f: Callable[..., Any]) -> Any:
        res = _decorators.prepare_serializer_decorator(f, allow_reuse)

        validator_wrapper_info = _decorators.SerializerDecoratorInfo(
            fields=fields,
            mode=mode,
            json_return_type=json_return_type,
            when_used=when_used,
            sub_path=sub_path,
            check_fields=check_fields,
        )
        return _decorators.PydanticDecoratorMarker(res, validator_wrapper_info, shim=lambda x: x)

    return dec
