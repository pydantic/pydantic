"""
This file is used to test pyright's ability to check Pydantic decorators used in `BaseModel`.
"""

from functools import partial, partialmethod
from typing import Any

from pydantic_core.core_schema import ValidatorFunctionWrapHandler
from typing_extensions import Self, assert_type

from pydantic import (
    BaseModel,
    FieldSerializationInfo,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    ValidationInfo,
    field_serializer,
    field_validator,
    model_serializer,
    model_validator,
)
from pydantic.functional_validators import ModelWrapValidatorHandler


def validate_before_func(value: Any) -> Any: ...


class BeforeModelValidator(BaseModel):
    @model_validator(mode='before')
    def valid_method(self, value: Any) -> Any:
        """TODO This shouldn't be valid. At runtime, `self` is the actual value and `value` is the `ValidationInfo` instance."""

    @model_validator(mode='before')
    def valid_method_info(self, value: Any, info: ValidationInfo) -> Any: ...

    @model_validator(mode='before')
    @classmethod
    def valid_classmethod(cls, value: Any) -> Any: ...

    @model_validator(mode='before')
    @staticmethod
    def valid_staticmethod(value: Any) -> Any: ...

    valid_function = model_validator(mode='before')(validate_before_func)


class WrapModelValidator(BaseModel):
    # mypy randomly does not catch the type error here (https://github.com/python/mypy/issues/18125)
    # so we also ignore the `unused-ignore` code:
    @model_validator(mode='wrap')  # type: ignore[arg-type, unused-ignore]  # pyright: ignore[reportArgumentType]
    def no_classmethod(cls, value: Any, handler: ModelWrapValidatorHandler[Self]) -> Self: ...

    @model_validator(mode='wrap')  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
    @classmethod
    def no_handler(cls, value: Any) -> Self: ...

    # Mypy somehow reports "Cannot infer function type argument" here:
    @model_validator(mode='wrap')  # type:ignore[misc]  # pyright: ignore[reportArgumentType]
    @classmethod
    def incompatible_type_var(cls, value: Any, handler: ModelWrapValidatorHandler[int]) -> int:
        """
        Type checkers will infer `cls` as being `type[Self]`.

        When binding the `incompatible_type_var` callable to `ModelWrapValidator.__call__`,
        the `_ModelType` type var will thus bind to `Self`. It is then expected to have
        `handler: ModelWrapValidatorHandler[_ModelType]` and the return type as `-> _ModelType`.
        """
        ...

    @model_validator(mode='wrap')
    @classmethod
    def valid_no_info(cls, value: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        rv = handler(value)
        assert_type(rv, Self)
        return rv

    @model_validator(mode='wrap')
    @classmethod
    def valid_info(cls, value: Any, handler: ModelWrapValidatorHandler[Self], info: ValidationInfo) -> Self:
        rv = handler(value, 1)
        assert_type(rv, Self)
        return rv


class AfterModelValidator(BaseModel):
    # Mypy somehow reports "Cannot infer function type argument" here:
    @model_validator(mode='after')  # type:ignore[misc]  # pyright: ignore[reportArgumentType]
    def missing_return_value(self) -> None: ...

    @model_validator(mode='after')
    def valid_method_no_info(self) -> Self: ...

    @model_validator(mode='after')
    def valid_method_info(self, info: ValidationInfo) -> Self: ...


class BeforeFieldValidator(BaseModel):
    """Same tests should apply to `mode='plain'`."""

    @field_validator('foo', mode='before')
    def no_classmethod(self, value: Any) -> Any:
        """TODO this shouldn't be valid, the decorator should only work on classmethods.

        We might want to do the same type checking as wrap model validators.
        """

    @field_validator('foo', mode='before')
    @classmethod
    def valid_classmethod(cls, value: Any) -> Any: ...

    @field_validator('foo', mode='before')  # type: ignore[type-var]  # pyright: ignore[reportArgumentType]
    @classmethod
    def invalid_with_info(cls, value: Any, info: int) -> Any: ...

    @field_validator('foo', mode='before', json_schema_input_type=int)  # `json_schema_input_type` allowed here.
    @classmethod
    def valid_with_info(cls, value: Any, info: ValidationInfo) -> Any: ...


class AfterFieldValidator(BaseModel):
    @field_validator('foo', mode='after')
    @classmethod
    def valid_classmethod(cls, value: Any) -> Any: ...

    @field_validator('foo', mode='after', json_schema_input_type=int)  # type: ignore[call-overload]  # pyright: ignore[reportCallIssue, reportArgumentType]
    @classmethod
    def invalid_input_type_not_allowed(cls, value: Any) -> Any: ...


class WrapFieldValidator(BaseModel):
    @field_validator('foo', mode='wrap')
    @classmethod
    def invalid_missing_handler(cls, value: Any) -> Any:
        """TODO This shouldn't be valid.

        At runtime, `check_decorator_fields_exist` raises an error, as the `handler` argument is missing.
        However, there's no type checking error as the provided signature matches
        `pydantic_core.core_schema.NoInfoWrapValidatorFunction`.
        """

    @field_validator('foo', mode='wrap')  # type: ignore[type-var]  # pyright: ignore[reportArgumentType]
    @classmethod
    def invalid_handler(cls, value: Any, handler: int) -> Any: ...

    @field_validator('foo', mode='wrap')
    @classmethod
    def valid_no_info(cls, value: Any, handler: ValidatorFunctionWrapHandler) -> Any: ...

    @field_validator('foo', mode='wrap', json_schema_input_type=int)  # `json_schema_input_type` allowed here.
    @classmethod
    def valid_with_info(cls, value: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo) -> Any: ...


class PlainModelSerializer(BaseModel):
    @model_serializer  # type: ignore[type-var]  # pyright: ignore[reportArgumentType]
    def too_many_arguments(self, info: SerializationInfo, unrelated: Any) -> Any: ...

    @model_serializer
    def valid_plain_serializer_1(self) -> Any: ...

    @model_serializer(mode='plain')
    def valid_plain_serializer_2(self) -> Any: ...

    @model_serializer(mode='plain')
    def valid_plain_serializer_info(self, info: SerializationInfo) -> Any: ...


class WrapModelSerializer(BaseModel):
    @model_serializer(mode='wrap')  # type: ignore[type-var]  # pyright: ignore[reportArgumentType]
    def no_handler(self) -> Any: ...

    @model_serializer(mode='wrap')
    def valid_no_info(self, handler: SerializerFunctionWrapHandler) -> Any:
        value = handler(self)
        return value

    @model_serializer(mode='wrap')
    def valid_info(self, handler: SerializerFunctionWrapHandler, info: SerializationInfo) -> Any:
        value = handler(self)
        return value


class PlainFieldSerializer(BaseModel):
    a: int = 1

    @field_serializer('a')
    def valid_method_no_info_1(self, value: Any) -> Any: ...

    @field_serializer('a', mode='plain')
    def valid_method_no_info_2(self, value: Any) -> Any: ...

    @field_serializer('a', mode='plain')  # type: ignore[type-var]  # pyright: ignore[reportArgumentType]
    def invalid_method_info_1(self, value: Any, info: int) -> Any: ...

    @field_serializer('a', mode='plain')
    def invalid_method_info_2(self, value: Any, info: SerializationInfo) -> Any:
        """TODO This shouldn't be valid.

        With field serializers, `info` is `FieldSerializationInfo`.
        However, the `AnyFieldPlainSerializer` type alias is too broad as it seems to include
        model serializer functions as well.

        This isn't trivial to solve, as we allow regular method and staticmethod/functions
        to be passed to `field_serializer`, so there's some overlaps in the signatures (because of the `self` argument).
        """

    @field_serializer('a', mode='plain')
    def valid_method_info(self, value: Any, info: FieldSerializationInfo) -> Any: ...

    @field_serializer('a', mode='plain')
    @staticmethod
    def valid_staticmethod_no_info(value: Any) -> Any: ...

    @field_serializer('a', mode='plain')
    @staticmethod
    def valid_staticmethod_info(value: Any, info: FieldSerializationInfo) -> Any: ...

    @field_serializer('a', mode='plain')
    @classmethod
    def valid_classmethod_no_info(cls, value: Any) -> Any: ...

    @field_serializer('a', mode='plain')
    @classmethod
    def valid_classmethod_info(cls, value: Any, info: FieldSerializationInfo) -> Any: ...

    partial_ = field_serializer('a', mode='plain')(partial(lambda v, x: v, x=1))

    def partial_method(self, value: Any, x: Any) -> Any: ...

    partial_method_ = field_serializer('a', mode='plain')(partialmethod(partial_method))


class WrapFieldSerializer(BaseModel):
    a: int = 1

    @field_serializer('a', mode='wrap')
    def no_handler(self, value: Any) -> Any:
        """TODO This shouldn't be valid.

        At runtime, `inspect_field_serializer` raises an error, as the `handler` argument is missing.
        However, there's no type checking error as the provided signature matches
        `pydantic_core.core_schema.GeneralWrapNoInfoSerializerFunction`.
        """

    @field_serializer('a', mode='wrap')  # type: ignore[type-var]  # pyright: ignore[reportArgumentType]
    @staticmethod
    def staticmethod_no_handler(value: Any) -> Any: ...

    @field_serializer('a', mode='wrap')
    def valid_no_info(self, value: Any, handler: SerializerFunctionWrapHandler) -> Any: ...

    @field_serializer('a', mode='wrap')
    def valid_info(self, value: Any, handler: SerializerFunctionWrapHandler, info: FieldSerializationInfo) -> Any: ...
