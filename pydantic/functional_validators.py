from __future__ import annotations as _annotations

import sys
from functools import partialmethod
from types import FunctionType
from typing import TYPE_CHECKING, Any, Callable, TypeVar, Union, overload

from pydantic_core import core_schema
from pydantic_core import core_schema as _core_schema
from typing_extensions import Literal, TypeAlias

from . import GetCoreSchemaHandler as _GetCoreSchemaHandler
from ._internal import _decorators, _internal_dataclass
from .errors import PydanticUserError

if sys.version_info < (3, 11):
    from typing_extensions import Protocol
else:
    from typing import Protocol

_inspect_validator = _decorators.inspect_validator


@_internal_dataclass.slots_dataclass(frozen=True)
class AfterValidator:
    '''A metadata class that indicates that a validation should be applied **after** the inner validation logic.

    Attributes:
        func: The validator function.

    Example:
        ```py
        from typing import Annotated

        from pydantic import BaseModel, AfterValidator, ValidationError


        MyInt = Annotated[int, AfterValidator(lambda v: v + 1)]

        class Model(BaseModel):
            a: MyInt

        print(Model(a=1).a)
        # > 2

        try:
            Model(a='a')
        except ValidationError as e:
            print(e.json(indent=2))
        """
        [
            {
                "type": "int_parsing",
                "loc": [
                    "a"
                ],
                "msg": "Input should be a valid integer, unable to parse string as an integer",
                "input": "a",
                "url": "https://errors.pydantic.dev/0.38.0/v/int_parsing"
            }
        ]
        """
        ```
    '''

    func: core_schema.NoInfoValidatorFunction | core_schema.GeneralValidatorFunction

    def __get_pydantic_core_schema__(self, source_type: Any, handler: _GetCoreSchemaHandler) -> core_schema.CoreSchema:
        schema = handler(source_type)
        info_arg = _inspect_validator(self.func, 'after')
        if info_arg:
            return core_schema.general_after_validator_function(self.func, schema=schema)  # type: ignore
        else:
            return core_schema.no_info_after_validator_function(self.func, schema=schema)  # type: ignore


@_internal_dataclass.slots_dataclass(frozen=True)
class BeforeValidator:
    """A metadata class that indicates that a validation should be applied **before** the inner validation logic.

    Example:
        ```py
        from typing import Annotated

        from pydantic import BaseModel, BeforeValidator


        MyInt = Annotated[int, BeforeValidator(lambda v: v + 1)]

        class Model(BaseModel):
            a: MyInt

        print(Model(a=1).a)
        # > 2

        try:
            Model(a='a')
        except TypeError as e:
            print(e)
            #> can only concatenate str (not "int") to str
        ```
    """

    func: core_schema.NoInfoValidatorFunction | core_schema.GeneralValidatorFunction

    def __get_pydantic_core_schema__(self, source_type: Any, handler: _GetCoreSchemaHandler) -> core_schema.CoreSchema:
        schema = handler(source_type)
        info_arg = _inspect_validator(self.func, 'before')
        if info_arg:
            return core_schema.general_before_validator_function(self.func, schema=schema)  # type: ignore
        else:
            return core_schema.no_info_before_validator_function(self.func, schema=schema)  # type: ignore


@_internal_dataclass.slots_dataclass(frozen=True)
class PlainValidator:
    """A metadata class that indicates that a validation should be applied **instead** of the inner validation logic.

    Example:
        ```py
        from typing import Annotated

        from pydantic import BaseModel, PlainValidator


        MyInt = Annotated[int, PlainValidator(lambda v: int(v) + 1)]

        class Model(BaseModel):
            a: MyInt

        print(Model(a='1').a)
        # > 2
        ```
    """

    func: core_schema.NoInfoValidatorFunction | core_schema.GeneralValidatorFunction

    def __get_pydantic_core_schema__(self, source_type: Any, handler: _GetCoreSchemaHandler) -> core_schema.CoreSchema:
        info_arg = _inspect_validator(self.func, 'plain')
        if info_arg:
            return core_schema.general_plain_validator_function(self.func)  # type: ignore
        else:
            return core_schema.no_info_plain_validator_function(self.func)  # type: ignore


@_internal_dataclass.slots_dataclass(frozen=True)
class WrapValidator:
    """A metadata class that indicates that a validation should be applied **around** the inner validation logic.

    ```py
    from datetime import datetime
    from typing import Annotated

    from pydantic import BaseModel, ValidationError, WrapValidator


    def validate_timestamp(v, handler):
        if v == "now":
            # we don't want to bother with further validation, just return the new value
            return datetime.now()
        try:
            return handler(v)
        except ValidationError:
            # validation failed, in this case we want to return a default value
            return datetime(2000, 1, 1)


    MyTimestamp = Annotated[datetime, WrapValidator(validate_timestamp)]


    class Model(BaseModel):
        a: MyTimestamp


    print(Model(a="now").a)
    # > 2023-01-22 23:10:00.000000
    print(Model(a="invalid").a)
    # > 2000-01-01 00:00:00.000000
    ```
    """

    func: core_schema.GeneralWrapValidatorFunction | core_schema.FieldWrapValidatorFunction

    def __get_pydantic_core_schema__(self, source_type: Any, handler: _GetCoreSchemaHandler) -> core_schema.CoreSchema:
        schema = handler(source_type)
        info_arg = _inspect_validator(self.func, 'wrap')
        if info_arg:
            return core_schema.general_wrap_validator_function(self.func, schema=schema)  # type: ignore
        else:
            return core_schema.no_info_wrap_validator_function(self.func, schema=schema)  # type: ignore


if TYPE_CHECKING:

    class _OnlyValueValidatorClsMethod(Protocol):
        def __call__(self, __cls: Any, __value: Any) -> Any:
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

    _V2Validator = Union[
        _V2ValidatorClsMethod,
        _core_schema.FieldValidatorFunction,
        _OnlyValueValidatorClsMethod,
        _core_schema.NoInfoValidatorFunction,
    ]

    _V2WrapValidator = Union[
        _V2WrapValidatorClsMethod,
        _core_schema.GeneralWrapValidatorFunction,
        _core_schema.FieldWrapValidatorFunction,
    ]

    _PartialClsOrStaticMethod: TypeAlias = Union[classmethod[Any, Any, Any], staticmethod[Any, Any], partialmethod[Any]]

    _V2BeforeAfterOrPlainValidatorType = TypeVar(
        '_V2BeforeAfterOrPlainValidatorType',
        _V2Validator,
        _PartialClsOrStaticMethod,
    )
    _V2WrapValidatorType = TypeVar('_V2WrapValidatorType', _V2WrapValidator, _PartialClsOrStaticMethod)


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
    """Decorate methods on the class indicating that they should be used to validate fields.

    Args:
        __field: The first field the field_validator should be called on; this is separate
            from `fields` to ensure an error is raised if you don't pass at least one.
        *fields: Additional field(s) the field_validator should be called on.
        mode: Specifies whether to validate the fields before or after validation.
             Defaults to 'after'.
        check_fields: If set to True, checks that the fields actually exist on the model.
            Defaults to None.

    Returns:
        A decorator that can be used to decorate a function to be used as a field_validator.
    """
    if isinstance(__field, FunctionType):
        raise PydanticUserError(
            '`@field_validator` should be used with fields and keyword arguments, not bare. '
            "E.g. usage should be `@validator('<field_name>', ...)`",
            code='validator-no-fields',
        )
    fields = __field, *fields
    if not all(isinstance(field, str) for field in fields):  # type: ignore
        raise PydanticUserError(
            '`@field_validator` fields should be passed as separate string args. '
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


_ModelType = TypeVar('_ModelType')
_ModelTypeCo = TypeVar('_ModelTypeCo', covariant=True)


class ModelWrapValidatorHandler(_core_schema.ValidatorFunctionWrapHandler, Protocol[_ModelTypeCo]):
    def __call__(self, input_value: Any, outer_location: str | int | None = None) -> _ModelTypeCo:  # pragma: no cover
        ...


class ModelWrapValidatorWithoutInfo(Protocol):
    def __call__(
        self,
        cls: type[_ModelType],
        # this can be a dict, a model instance
        # or anything else that gets passed to validate_python
        # thus validators _must_ handle all cases
        __value: Any,
        __handler: ModelWrapValidatorHandler[_ModelType],
    ) -> _ModelType:
        ...


class ModelWrapValidator(Protocol):
    def __call__(
        self,
        cls: type[_ModelType],
        # this can be a dict, a model instance
        # or anything else that gets passed to validate_python
        # thus validators _must_ handle all cases
        __value: Any,
        __handler: ModelWrapValidatorHandler[_ModelType],
        __info: _core_schema.ValidationInfo,
    ) -> _ModelType:
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
        self: _ModelType,  # type: ignore
    ) -> _ModelType:
        ...


class ModelAfterValidator(Protocol):
    @staticmethod
    def __call__(
        self: _ModelType,  # type: ignore
        __info: _core_schema.ValidationInfo,
    ) -> _ModelType:
        ...


_AnyModelWrapValidator = Union[ModelWrapValidator, ModelWrapValidatorWithoutInfo]
_AnyModeBeforeValidator = Union[ModelBeforeValidator, ModelBeforeValidatorWithoutInfo]
_AnyModeAfterValidator = Union[ModelAfterValidator, ModelAfterValidatorWithoutInfo]


@overload
def model_validator(
    *,
    mode: Literal['wrap'],
) -> Callable[[_AnyModelWrapValidator], _decorators.PydanticDescriptorProxy[_decorators.ModelValidatorDecoratorInfo]]:
    ...


@overload
def model_validator(
    *,
    mode: Literal['before'],
) -> Callable[[_AnyModeBeforeValidator], _decorators.PydanticDescriptorProxy[_decorators.ModelValidatorDecoratorInfo]]:
    ...


@overload
def model_validator(
    *,
    mode: Literal['after'],
) -> Callable[[_AnyModeAfterValidator], _decorators.PydanticDescriptorProxy[_decorators.ModelValidatorDecoratorInfo]]:
    ...


def model_validator(
    *,
    mode: Literal['wrap', 'before', 'after'],
) -> Any:
    """Decorate model methods for validation purposes.

    Args:
        mode: A required string literal that specifies the validation mode.
            It can be one of the following: 'wrap', 'before', or 'after'.

    Returns:
        A decorator that can be used to decorate a function to be used as a model validator.
    """

    def dec(f: Any) -> _decorators.PydanticDescriptorProxy[Any]:
        # auto apply the @classmethod decorator
        f = _decorators.ensure_classmethod_based_on_signature(f)
        dec_info = _decorators.ModelValidatorDecoratorInfo(mode=mode)
        return _decorators.PydanticDescriptorProxy(f, dec_info)

    return dec
