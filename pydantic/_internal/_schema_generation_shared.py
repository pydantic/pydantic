"""Types and utility functions used by various other internal tools."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable, Literal, cast

from pydantic_core import core_schema

from ..annotated_handlers import GetCoreSchemaHandler, GetJsonSchemaHandler

if TYPE_CHECKING:
    from ..json_schema import GenerateJsonSchema, JsonRef, JsonSchemaValue
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

    def __init__(
        self,
        generate_json_schema: GenerateJsonSchema,
        handler_override: HandlerOverride | None,
        *,
        mark_user_definition: bool = False,
    ) -> None:
        self.generate_json_schema = generate_json_schema
        self.handler = handler_override or generate_json_schema.generate_inner
        self.mode = generate_json_schema.mode
        self.mark_user_definition = mark_user_definition

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
        mark_user_definition = self.mark_user_definition
        if '$ref' not in maybe_ref_json_schema:
            if mark_user_definition:
                state_info = self.generate_json_schema._find_state_for_canonical_schema(maybe_ref_json_schema)
                if state_info is not None:
                    defs_ref, state = state_info
                    state.pending = True
                    state.schema = maybe_ref_json_schema
            return maybe_ref_json_schema
        ref = maybe_ref_json_schema['$ref']
        json_ref = cast('JsonRef', ref)
        defs_ref = self.generate_json_schema.json_to_defs_refs.get(json_ref)
        json_schema = self.generate_json_schema.get_schema_from_definitions(ref, root=maybe_ref_json_schema)
        if json_schema is None:
            raise LookupError(
                f'Could not find a ref for {ref}.'
                ' Maybe you tried to call resolve_ref_schema from within a recursive model?'
            )
        if mark_user_definition:
            wrapper_schema = deepcopy(maybe_ref_json_schema)
            if defs_ref is not None:
                state = self.generate_json_schema._get_user_definition_state(defs_ref)
                state.pending = True
                state.schema = json_schema
                state.wrappers.setdefault(json_ref, wrapper_schema)
                tokens = self.generate_json_schema._json_pointer_tokens(json_ref)
                if len(tokens) >= 2:
                    parent_tokens: tuple[str, ...] | None = None
                    for index in range(len(tokens) - 1):
                        if tokens[index] == '$defs':
                            name_index = index + 1
                            if name_index < len(tokens):
                                parent_tokens = tuple(tokens[: name_index + 1])
                            break
                    if parent_tokens is not None:
                        parent_ref = self.generate_json_schema._json_pointer_from_tokens(parent_tokens)
                        parent_defs_ref = self.generate_json_schema.json_to_defs_refs.get(parent_ref)
                        if parent_defs_ref is not None and wrapper_schema.get('$ref') == parent_ref:
                            parent_state = self.generate_json_schema._get_user_definition_state(parent_defs_ref)
                            parent_state.wrappers.setdefault(parent_ref, wrapper_schema)
            else:
                state_info = self.generate_json_schema._find_state_for_canonical_schema(json_schema)
                if state_info is not None:
                    defs_ref, state = state_info
                    state.pending = True
                    state.schema = json_schema
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
        if self._ref_mode == 'to-def':
            ref = schema.get('ref')
            if ref is not None:
                return self._generate_schema.defs.create_definition_reference_schema(schema)
            return schema
        else:  # ref_mode = 'unpack'
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
            definition = self._generate_schema.defs.get_schema_from_ref(ref)
            if definition is None:
                raise LookupError(
                    f'Could not find a ref for {ref}.'
                    ' Maybe you tried to call resolve_ref_schema from within a recursive model?'
                )
            return definition
        elif maybe_ref_schema['type'] == 'definitions':
            return self.resolve_ref_schema(maybe_ref_schema['schema'])
        return maybe_ref_schema
