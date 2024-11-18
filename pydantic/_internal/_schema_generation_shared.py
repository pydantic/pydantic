"""Types and utility functions used by various other internal tools."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, Callable

from pydantic_core import core_schema
from typing_extensions import Literal

from ..annotated_handlers import GetCoreSchemaHandler, GetJsonSchemaHandler

if TYPE_CHECKING:
    from ..json_schema import GenerateJsonSchema, JsonSchemaValue
    from ._core_utils import CoreSchemaOrField
    from ._generate_schema import GenerateSchema
    from ._namespace_utils import NamespacesTuple

    GetJsonSchemaFunction = Callable[[CoreSchemaOrField, GetJsonSchemaHandler], JsonSchemaValue]
    HandlerOverride = Callable[[CoreSchemaOrField], JsonSchemaValue]


class GenerateJsonSchemaHandler(GetJsonSchemaHandler):
    """JsonSchemaHandler implementation that doesn't do ref unwrapping by default.

    This is used for any Annotated metadata so that we don't end up with conflicting
    modifications to the definition schema.

    Used internally by Pydantic, please do not rely on this implementation.
    See `GetJsonSchemaHandler` for the handler API.
    """

    def __init__(self, generate_json_schema: GenerateJsonSchema, handler_override: HandlerOverride | None) -> None:
        self.generate_json_schema = generate_json_schema
        self.handler = handler_override or generate_json_schema.generate_inner
        self.mode = generate_json_schema.mode

    def __call__(self, core_schema: CoreSchemaOrField, /) -> JsonSchemaValue:
        return self.handler(core_schema)

    def resolve_ref_schema(self, maybe_ref_json_schema: JsonSchemaValue) -> JsonSchemaValue:
        """Resolves `$ref` in the json schema.

        This returns the input json schema if there is no `$ref` in json schema.

        Args:
            maybe_ref_json_schema: The input json schema that may contains `$ref`.

        Returns:
            Resolved json schema.

        Raises:
            LookupError: If it can't find the definition for `$ref`.
        """
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
    """Wrapper to use an arbitrary function as a `GetCoreSchemaHandler`.

    Used internally by Pydantic, please do not rely on this implementation.
    See `GetCoreSchemaHandler` for the handler API.
    """

    def __init__(
        self,
        handler: Callable[[Any], core_schema.CoreSchema],
        generate_schema: GenerateSchema,
        ref_mode: Literal['to-def', 'unpack'] = 'to-def',
    ) -> None:
        self._handler = handler
        self._generate_schema = generate_schema
        self._ref_mode = ref_mode

    def __call__(self, source_type: Any, /) -> core_schema.CoreSchema:
        schema = self._handler(source_type)
        ref = schema.get('ref')
        if self._ref_mode == 'to-def':
            if ref is not None:
                self._generate_schema.defs.definitions[ref] = schema
                return core_schema.definition_reference_schema(ref)
            return schema
        else:  # ref_mode = 'unpack
            return self.resolve_ref_schema(schema)

    def _get_types_namespace(self) -> NamespacesTuple:
        return self._generate_schema._types_namespace

    def generate_schema(self, source_type: Any, /) -> core_schema.CoreSchema:
        return self._generate_schema.generate_schema(source_type)

    @property
    def field_name(self) -> str | None:
        return self._generate_schema.field_name_stack.get()

    def resolve_ref_schema(self, maybe_ref_schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
        """Resolves reference in the core schema.

        Args:
            maybe_ref_schema: The input core schema that may contains reference.

        Returns:
            Resolved core schema.

        Raises:
            LookupError: If it can't find the definition for reference.
        """
        if maybe_ref_schema['type'] == 'definition-ref':
            ref = maybe_ref_schema['schema_ref']
            if ref not in self._generate_schema.defs.definitions:
                raise LookupError(
                    f'Could not find a ref for {ref}.'
                    ' Maybe you tried to call resolve_ref_schema from within a recursive model?'
                )
            return self._generate_schema.defs.definitions[ref]
        elif maybe_ref_schema['type'] == 'definitions':
            return self.resolve_ref_schema(maybe_ref_schema['schema'])
        return maybe_ref_schema


def get_schema_or_set_mocks(
    schema_container: Any,
    schema_type: Any,
    set_mocks: Callable[..., None],  # we use a ... here bc optionality is handled by the caller
    gen_schema: GenerateSchema,
    raise_errors: bool,
    get_schema: Callable[[Any, GetCoreSchemaHandler], core_schema.CoreSchema] | None = None,
) -> core_schema.CoreSchema | None:
    """Get and return the core schema associated with `schema_type`.
    If the schema is not found and `raise_errors` is `False`, set mocks on `schema_container` and return `None`.

    Args:
        schema_container: The container to set mocks on if the schema is not found (either a model, dataclass, or TypeAdapter instance).
        schema_type: The type to get the schema for (a model, dataclass, or TypeAdapter's embedded type).
        set_mocks: The function to set mocks on `schema_container`.
        gen_schema: The `GenerateSchema` instance to use to generate the schema.
        raise_errors: Whether to raise errors if the schema cannot be generated.
        get_schema: The optional `__get_pydantic_core_schema__` method to use to get the schema, with priority over `gen_schema`.
    """
    from ..errors import PydanticUndefinedAnnotation

    try:
        if get_schema:
            schema = get_schema(
                schema_type,
                CallbackGetCoreSchemaHandler(
                    partial(gen_schema.generate_schema, from_dunder_get_core_schema=False),
                    gen_schema,
                    ref_mode='unpack',
                ),
            )
        else:
            schema = gen_schema.generate_schema(schema_type, from_dunder_get_core_schema=False)
    except PydanticUndefinedAnnotation as e:
        if raise_errors:
            raise
        set_mocks(schema_container, f'`{e.name}`')
        return None

    try:
        schema = gen_schema.clean_schema(schema)
    except gen_schema.CollectedInvalid:
        set_mocks(schema_container)
        return None
