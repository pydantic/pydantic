from dataclasses import dataclass, field
from typing import TypedDict

from pydantic_core.core_schema import CoreSchema, DefinitionReferenceSchema, SerSchema


class GatherResult(TypedDict):
    """Schema traversing result."""

    collected_references: dict[str, DefinitionReferenceSchema | None]
    """The collected definition references.

    If a definition reference schema can be inlined, it means that there is
    only one in the whole core schema. As such, it is stored as the value.
    Otherwise, the value is set to `None`.
    """

    deferred_discriminator_schemas: list[CoreSchema]
    """The list of core schemas having the discriminator application deferred."""


class MissingDefinitionError(LookupError):
    """A reference was pointing to a non-existing core schema."""

    def __init__(self, schema_reference: str, /) -> None:
        self.schema_reference = schema_reference


@dataclass
class GatherContext:
    """The current context used during core schema traversing.

    Context instances should only be used during schema traversing.
    """

    definitions: dict[str, CoreSchema]
    """The available definitions."""

    deferred_discriminator_schemas: list[CoreSchema] = field(init=False, default_factory=list)
    """The list of core schemas having the discriminator application deferred.

    Internally, these core schemas have a specific key set in the core metadata dict.
    """

    collected_references: dict[str, DefinitionReferenceSchema | None] = field(init=False, default_factory=dict)
    """The collected definition references.

    If a definition reference schema can be inlined, it means that there is
    only one in the whole core schema. As such, it is stored as the value.
    Otherwise, the value is set to `None`.

    During schema traversing, definition reference schemas can be added as candidates, or removed
    (by setting the value to `None`).
    """


def gather_meta(schema: CoreSchema, ctx: GatherContext) -> None:
    meta = schema.get('metadata')
    if meta is not None and 'pydantic_internal_union_discriminator' in meta:
        ctx.deferred_discriminator_schemas.append(schema)


def gather_definition_ref(def_ref_schema: DefinitionReferenceSchema, ctx: GatherContext) -> None:
    schema_ref = def_ref_schema['schema_ref']

    if schema_ref not in ctx.collected_references:
        definition = ctx.definitions.get(schema_ref)
        if definition is None:
            raise MissingDefinitionError(schema_ref)

        # The `'definition-ref'` schema was only encountered once, make it
        # a candidate to be inlined:
        ctx.collected_references[schema_ref] = def_ref_schema
        gather_schema(definition, ctx)
        if 'serialization' in def_ref_schema:
            gather_schema(def_ref_schema['serialization'], ctx)
        gather_meta(def_ref_schema, ctx)
    else:
        # The `'definition-ref'` schema was already encountered, meaning
        # the previously encountered schema (and this one) can't be inlined:
        ctx.collected_references[schema_ref] = None


def gather_schema(schema: CoreSchema | SerSchema, context: GatherContext) -> None:
    match schema['type']:
        case 'definition-ref':
            gather_definition_ref(schema, context)
            return
        case 'definitions':
            gather_schema(schema['schema'], context)
            for definition in schema['definitions']:
                gather_schema(definition, context)
        case 'list' | 'set' | 'frozenset' | 'generator':
            if 'items_schema' in schema:
                gather_schema(schema['items_schema'], context)
        case 'tuple':
            if 'items_schema' in schema:
                for s in schema['items_schema']:
                    gather_schema(s, context)
        case 'dict':
            if 'keys_schema' in schema:
                gather_schema(schema['keys_schema'], context)
            if 'values_schema' in schema:
                gather_schema(schema['values_schema'], context)
        case 'union':
            for choice in schema['choices']:
                if isinstance(choice, tuple):
                    gather_schema(choice[0], context)
                else:
                    gather_schema(choice, context)
        case 'tagged-union':
            for v in schema['choices'].values():
                gather_schema(v, context)
        case 'chain':
            for step in schema['steps']:
                gather_schema(step, context)
        case 'lax-or-strict':
            gather_schema(schema['lax_schema'], context)
            gather_schema(schema['strict_schema'], context)
        case 'json-or-python':
            gather_schema(schema['json_schema'], context)
            gather_schema(schema['python_schema'], context)
        case 'model-fields' | 'typed-dict':
            if 'extras_schema' in schema:
                gather_schema(schema['extras_schema'], context)
            if 'computed_fields' in schema:
                for s in schema['computed_fields']:
                    gather_schema(s, context)
            for s in schema['fields'].values():
                gather_schema(s, context)
        case 'dataclass-args':
            if 'computed_fields' in schema:
                for s in schema['computed_fields']:
                    gather_schema(s, context)
            for s in schema['fields']:
                gather_schema(s, context)
        case 'arguments':
            for s in schema['arguments_schema']:
                gather_schema(s['schema'], context)
            if 'var_args_schema' in schema:
                gather_schema(schema['var_args_schema'], context)
            if 'var_kwargs_schema' in schema:
                gather_schema(schema['var_kwargs_schema'], context)
        case 'call':
            gather_schema(schema['arguments_schema'], context)
            if 'return_schema' in schema:
                gather_schema(schema['return_schema'], context)
        case 'computed-field' | 'function-plain':
            if 'return_schema' in schema:
                gather_schema(schema['return_schema'], context)
            if 'json_schema_input_schema' in schema:
                gather_schema(schema['json_schema_input_schema'], context)
        case 'function-wrap':
            if 'return_schema' in schema:
                gather_schema(schema['return_schema'], context)
            if 'schema' in schema:
                gather_schema(schema['schema'], context)
        case _:
            if 'schema' in schema:
                gather_schema(schema['schema'], context)

    if 'serialization' in schema:
        gather_schema(schema['serialization'], context)
    gather_meta(schema, context)


def gather_schemas_for_cleaning(schema: CoreSchema, definitions: dict[str, CoreSchema]) -> GatherResult:
    """Traverse the core schema and definitions and return the necessary information for schema cleaning.

    During the core schema traversing, any `'definition-ref'` schema is:

    - Validated: the reference must point to an existing definition. If this is not the case, a
      `MissingDefinitionError` exception is raised.
    - Stored in the context: the actual reference is stored in the context. Depending on whether
      the `'definition-ref'` schema is encountered twice or only once, the schema itself is also
      saved in the context to be inlined (i.e. replaced by the definition it points to).
    """
    context = GatherContext(definitions)
    gather_schema(schema, context)

    return {
        'collected_references': context.collected_references,
        'deferred_discriminator_schemas': context.deferred_discriminator_schemas,
    }
