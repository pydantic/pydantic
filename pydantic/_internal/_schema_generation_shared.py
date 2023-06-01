"""
Types and utility functions used by various other internal tools.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from pydantic_core import core_schema

from ._annotated_handlers import GetCoreSchemaHandler, GetJsonSchemaHandler

if TYPE_CHECKING:
    from ..json_schema import GenerateJsonSchema, JsonSchemaValue
    from ._core_utils import CoreSchemaOrField

    GetJsonSchemaFunction = Callable[[CoreSchemaOrField, GetJsonSchemaHandler], JsonSchemaValue]
    HandlerOverride = Callable[[CoreSchemaOrField], JsonSchemaValue]


class UnpackedRefJsonSchemaHandler(GetJsonSchemaHandler):
    """
    A GetJsonSchemaHandler implementation that automatically unpacks `$ref`
    schemas so that the caller doesn't have to worry about that.

    This is used for custom types and models that implement `__get_pydantic_core_schema__`
    so they always get a `non-$ref` schema.

    Used internally by Pydantic, please do not rely on this implementation.
    See `GetJsonSchemaHandler` for the handler API.
    """

    original_schema: JsonSchemaValue | None = None

    def __init__(self, handler: GetJsonSchemaHandler) -> None:
        self.handler = handler
        self.mode = handler.mode

    def resolve_ref_schema(self, __maybe_ref_json_schema: JsonSchemaValue) -> JsonSchemaValue:
        return self.handler.resolve_ref_schema(__maybe_ref_json_schema)

    def __call__(self, core_schema: CoreSchemaOrField) -> JsonSchemaValue:
        self.original_schema = self.handler(core_schema)
        return self.resolve_ref_schema(self.original_schema)

    def update_schema(self, schema: JsonSchemaValue) -> JsonSchemaValue:
        if self.original_schema is None:
            # handler / our __call__ was never called
            return schema
        if '$ref' in self.original_schema:
            original_referenced_schema = self.resolve_ref_schema(self.original_schema)
            if schema != original_referenced_schema:
                # a new schema was returned, update the non-ref schema
                original_referenced_schema.clear()
                original_referenced_schema.update(schema)
            # return self.original_schema, which may be a ref schema
            return self.original_schema
        # not a ref schema, return the new schema
        return schema


def wrap_json_schema_fn_for_model_or_custom_type_with_ref_unpacking(
    fn: GetJsonSchemaFunction,
) -> GetJsonSchemaFunction:
    def wrapped(schema_or_field: CoreSchemaOrField, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        wrapped_handler = UnpackedRefJsonSchemaHandler(handler)
        json_schema = fn(schema_or_field, wrapped_handler)
        json_schema = wrapped_handler.update_schema(json_schema)
        return json_schema

    return wrapped


class GenerateJsonSchemaHandler(GetJsonSchemaHandler):
    """
    JsonSchemaHandler implementation that doesn't do ref unwrapping by default.

    This is used for any Annotated metadata so that we don't end up with conflicting
    modifications to the definition schema.

    Used internally by Pydantic, please do not rely on this implementation.
    See `GetJsonSchemaHandler` for the handler API.
    """

    def __init__(self, generate_json_schema: GenerateJsonSchema, handler_override: HandlerOverride | None) -> None:
        self.generate_json_schema = generate_json_schema
        self.handler = handler_override or generate_json_schema.generate_inner
        self.mode = generate_json_schema.mode

    def __call__(self, __core_schema: CoreSchemaOrField) -> JsonSchemaValue:
        return self.handler(__core_schema)

    def resolve_ref_schema(self, maybe_ref_json_schema: JsonSchemaValue) -> JsonSchemaValue:
        if '$ref' not in maybe_ref_json_schema:
            return maybe_ref_json_schema
        ref = maybe_ref_json_schema['$ref']
        json_schema = self.generate_json_schema.get_schema_from_definitions(ref)
        if json_schema is None:
            raise LookupError(
                f'Could not find a ref for {ref}.'
                ' Maybe you tried to call resolve_ref_schema from within a recursive model?'
            )
        return json_schema


class CallbackGetCoreSchemaHandler(GetCoreSchemaHandler):
    """
    Wrapper to use an arbitrary function as a `GetCoreSchemaHandler`.

    Used internally by Pydantic, please do not rely on this implementation.
    See `GetCoreSchemaHandler` for the handler API.
    """

    def __init__(
        self, handler: Callable[[Any], core_schema.CoreSchema], generate_schema: Callable[[Any], core_schema.CoreSchema]
    ) -> None:
        self._handler = handler
        self._generate_schema = generate_schema

    def __call__(self, __source_type: Any) -> core_schema.CoreSchema:
        return self._handler(__source_type)

    def generate_schema(self, __source_type: Any) -> core_schema.CoreSchema:
        return self._generate_schema(__source_type)
