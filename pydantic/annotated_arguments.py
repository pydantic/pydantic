from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, TypeVar

from pydantic_core import core_schema
from typing_extensions import Annotated, Literal

from ._internal._core_metadata import build_metadata_dict
from ._internal._decorators import inspect_annotated_serializer, inspect_validator
from ._internal._internal_dataclass import slots_dataclass
from .annotated import GetCoreSchemaHandler


@slots_dataclass(frozen=True)
class AfterValidator:
    func: core_schema.NoInfoValidatorFunction | core_schema.GeneralValidatorFunction

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        schema = handler(source_type)
        info_arg = inspect_validator(self.func, 'after')
        if info_arg:
            return core_schema.general_after_validator_function(self.func, schema=schema)  # type: ignore
        else:
            return core_schema.no_info_after_validator_function(self.func, schema=schema)  # type: ignore


@slots_dataclass(frozen=True)
class BeforeValidator:
    func: core_schema.NoInfoValidatorFunction | core_schema.GeneralValidatorFunction

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        schema = handler(source_type)
        info_arg = inspect_validator(self.func, 'before')
        if info_arg:
            return core_schema.general_before_validator_function(self.func, schema=schema)  # type: ignore
        else:
            return core_schema.no_info_before_validator_function(self.func, schema=schema)  # type: ignore


@slots_dataclass(frozen=True)
class PlainValidator:
    func: core_schema.NoInfoValidatorFunction | core_schema.GeneralValidatorFunction

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        info_arg = inspect_validator(self.func, 'plain')
        if info_arg:
            return core_schema.general_plain_validator_function(self.func)  # type: ignore
        else:
            return core_schema.no_info_plain_validator_function(self.func)  # type: ignore


@slots_dataclass(frozen=True)
class WrapValidator:
    func: core_schema.GeneralWrapValidatorFunction | core_schema.FieldWrapValidatorFunction

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        schema = handler(source_type)
        info_arg = inspect_validator(self.func, 'wrap')
        if info_arg:
            return core_schema.general_wrap_validator_function(self.func, schema=schema)  # type: ignore
        else:
            return core_schema.no_info_wrap_validator_function(self.func, schema=schema)  # type: ignore


@slots_dataclass(frozen=True)
class PlainSerializer:
    func: core_schema.SerializerFunction
    json_return_type: core_schema.JsonReturnTypes | None = None
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always'

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        schema = handler(source_type)
        schema['serialization'] = core_schema.plain_serializer_function_ser_schema(
            function=self.func,
            info_arg=inspect_annotated_serializer(self.func, 'plain'),
            json_return_type=self.json_return_type,
            when_used=self.when_used,
        )
        return schema


@slots_dataclass(frozen=True)
class WrapSerializer:
    func: core_schema.WrapSerializerFunction
    json_return_type: core_schema.JsonReturnTypes | None = None
    when_used: Literal['always', 'unless-none', 'json', 'json-unless-none'] = 'always'

    def __get_pydantic_core_schema__(self, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        schema = handler(source_type)
        schema['serialization'] = core_schema.wrap_serializer_function_ser_schema(
            function=self.func,
            info_arg=inspect_annotated_serializer(self.func, 'wrap'),
            json_return_type=self.json_return_type,
            when_used=self.when_used,
        )
        return schema


AnyType = TypeVar('AnyType')
if TYPE_CHECKING:
    SkipValidation = Annotated[AnyType, ...]  # SkipValidation[list[str]] will be treated by type checkers as list[str]
else:

    class SkipValidation:
        """
        If this is applied as an annotation (e.g., via `x: Annotated[int, SkipValidation]`), validation will be skipped.

        This can be useful if you want to use a type annotation for documentation/IDE/type-checking purposes,
        and know that it is safe to skip validation for one or more of the fields.

        Because this converts the validation schema to `any_schema`, subsequent annotation-applied transformations
        may not have the expected effects. Therefore, when used, this annotation should generally be the final
        annotation applied to a type.

        You can also use `SkipValidation[int]` as a shorthand for `Annotated[int, SkipValidation]`.
        """

        def __class_getitem__(cls, item: Any) -> Any:
            return Annotated[item, SkipValidation]

        @classmethod
        def __get_pydantic_core_schema__(
            cls, _source: Any, _handler: Callable[[Any], core_schema.CoreSchema]
        ) -> core_schema.CoreSchema:
            original_schema = _handler(_source)
            metadata = build_metadata_dict(js_functions=[lambda _c, h: h(original_schema)])
            return core_schema.any_schema(metadata=metadata, serialization=original_schema.get('serialization'))
