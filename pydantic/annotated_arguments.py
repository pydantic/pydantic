from __future__ import annotations

from typing import Any, Callable

from pydantic_core import core_schema
from typing_extensions import Literal

from ._internal._decorators import inspect_annotated_serializer, inspect_validator
from ._internal._internal_dataclass import slots_dataclass


@slots_dataclass
class AfterValidator:
    func: core_schema.NoInfoValidatorFunction | core_schema.GeneralValidatorFunction

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: Callable[[Any], core_schema.CoreSchema]
    ) -> core_schema.CoreSchema:
        schema = handler(source_type)
        info_arg = inspect_validator(self.func, 'after')
        if info_arg:
            return core_schema.general_after_validator_function(self.func, schema=schema)  # type: ignore
        else:
            return core_schema.no_info_after_validator_function(self.func, schema=schema)  # type: ignore


@slots_dataclass
class BeforeValidator:
    func: core_schema.NoInfoValidatorFunction | core_schema.GeneralValidatorFunction

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: Callable[[Any], core_schema.CoreSchema]
    ) -> core_schema.CoreSchema:
        schema = handler(source_type)
        info_arg = inspect_validator(self.func, 'before')
        if info_arg:
            return core_schema.general_before_validator_function(self.func, schema=schema)  # type: ignore
        else:
            return core_schema.no_info_before_validator_function(self.func, schema=schema)  # type: ignore


@slots_dataclass
class PlainValidator:
    func: core_schema.NoInfoValidatorFunction | core_schema.GeneralValidatorFunction

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: Callable[[Any], core_schema.CoreSchema]
    ) -> core_schema.CoreSchema:
        schema = handler(source_type)
        info_arg = inspect_validator(self.func, 'plain')
        if info_arg:
            return core_schema.general_plain_validator_function(self.func, schema=schema)  # type: ignore
        else:
            return core_schema.no_info_plain_validator_function(self.func, schema=schema)  # type: ignore


@slots_dataclass
class WrapValidator:
    func: core_schema.GeneralWrapValidatorFunction | core_schema.FieldWrapValidatorFunction

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: Callable[[Any], core_schema.CoreSchema]
    ) -> core_schema.CoreSchema:
        schema = handler(source_type)
        info_arg = inspect_validator(self.func, 'wrap')
        if info_arg:
            return core_schema.general_wrap_validator_function(self.func, schema=schema)  # type: ignore
        else:
            return core_schema.no_info_wrap_validator_function(self.func, schema=schema)  # type: ignore


@slots_dataclass
class PlainSerializer:
    func: core_schema.SerializerFunction
    json_return_type: core_schema.JsonReturnTypes | None = None
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always'

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: Callable[[Any], core_schema.CoreSchema]
    ) -> core_schema.CoreSchema:
        schema = handler(source_type)
        schema['serialization'] = core_schema.plain_serializer_function_ser_schema(
            function=self.func,
            info_arg=inspect_annotated_serializer(self.func, 'plain'),
            json_return_type=self.json_return_type,
            when_used=self.when_used,
        )
        return schema


@slots_dataclass
class WrapSerializer:
    func: core_schema.WrapSerializerFunction
    json_return_type: core_schema.JsonReturnTypes | None = None
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always'

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: Callable[[Any], core_schema.CoreSchema]
    ) -> core_schema.CoreSchema:
        schema = handler(source_type)
        schema['serialization'] = core_schema.wrap_serializer_function_ser_schema(
            function=self.func,
            info_arg=inspect_annotated_serializer(self.func, 'wrap'),
            json_return_type=self.json_return_type,
            when_used=self.when_used,
        )
        return schema
