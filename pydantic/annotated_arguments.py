from __future__ import annotations

from typing import Any, Callable

from pydantic_core import core_schema
from typing_extensions import Literal

from ._internal._decorators import check_if_annotated_serializer_requires_info_arg, check_if_validator_requires_info_arg
from ._internal._internal_dataclass import slots_dataclass


@slots_dataclass
class AfterValidator:
    func: core_schema.NoInfoValidatorFunction | core_schema.GeneralValidatorFunction

    def __modify_pydantic_core_schema__(
        self, _source: Any, handler: Callable[[], core_schema.CoreSchema]
    ) -> core_schema.CoreSchema:
        info_arg = check_if_validator_requires_info_arg(self.func, 'after')
        if info_arg:
            return core_schema.general_after_validator_function(self.func, schema=handler())  # type: ignore
        else:
            return core_schema.no_info_after_validator_function(self.func, schema=handler())  # type: ignore


@slots_dataclass
class BeforeValidator:
    func: core_schema.NoInfoValidatorFunction | core_schema.GeneralValidatorFunction

    def __modify_pydantic_core_schema__(
        self, _source: Any, handler: Callable[[], core_schema.CoreSchema]
    ) -> core_schema.CoreSchema:
        info_arg = check_if_validator_requires_info_arg(self.func, 'before')
        if info_arg:
            return core_schema.general_before_validator_function(self.func, schema=handler())  # type: ignore
        else:
            return core_schema.no_info_before_validator_function(self.func, schema=handler())  # type: ignore


@slots_dataclass
class PlainValidator:
    func: core_schema.NoInfoValidatorFunction | core_schema.GeneralValidatorFunction

    def __modify_pydantic_core_schema__(
        self, _source: Any, handler: Callable[[], core_schema.CoreSchema]
    ) -> core_schema.CoreSchema:
        info_arg = check_if_validator_requires_info_arg(self.func, 'plain')
        if info_arg:
            return core_schema.general_plain_validator_function(self.func, schema=handler())  # type: ignore
        else:
            return core_schema.no_info_plain_validator_function(self.func, schema=handler())  # type: ignore


@slots_dataclass
class WrapValidator:
    func: core_schema.GeneralWrapValidatorFunction | core_schema.FieldWrapValidatorFunction

    def __modify_pydantic_core_schema__(
        self, _source: Any, handler: Callable[[], core_schema.CoreSchema]
    ) -> core_schema.CoreSchema:
        info_arg = check_if_validator_requires_info_arg(self.func, 'wrap')
        if info_arg:
            return core_schema.general_wrap_validator_function(self.func, schema=handler())  # type: ignore
        else:
            return core_schema.no_info_wrap_validator_function(self.func, schema=handler())  # type: ignore


@slots_dataclass
class PlainSerializer:
    func: core_schema.SerializerFunction
    json_return_type: core_schema.JsonReturnTypes | None = None
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always'

    def __modify_pydantic_core_schema__(
        self, _source: Any, handler: Callable[[], core_schema.CoreSchema]
    ) -> core_schema.CoreSchema:
        schema = handler()
        schema['serialization'] = core_schema.plain_serializer_function_ser_schema(
            function=self.func,
            info_arg=check_if_annotated_serializer_requires_info_arg(self.func, 'plain'),
            json_return_type=self.json_return_type,
            when_used=self.when_used,
        )
        return schema


@slots_dataclass
class WrapSerializer:
    func: core_schema.WrapSerializerFunction
    json_return_type: core_schema.JsonReturnTypes | None = None
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always'

    def __modify_pydantic_core_schema__(
        self, _source: Any, handler: Callable[[], core_schema.CoreSchema]
    ) -> core_schema.CoreSchema:
        schema = handler()
        schema['serialization'] = core_schema.wrap_serializer_function_ser_schema(
            function=self.func,
            info_arg=check_if_annotated_serializer_requires_info_arg(self.func, 'wrap'),
            json_return_type=self.json_return_type,
            when_used=self.when_used,
        )
        return schema
