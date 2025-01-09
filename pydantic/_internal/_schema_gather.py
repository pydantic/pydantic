from collections import defaultdict
from typing import TypedDict

from pydantic_core.core_schema import CoreSchema, DefinitionReferenceSchema, SerSchema


class GatherResult(TypedDict):
    """Internal result of gathering schemas for cleaning."""

    inlinable_def_refs: dict[str, DefinitionReferenceSchema | None]
    recursive_refs: set[str]
    schemas_with_meta_keys: dict[str, list[CoreSchema]] | None


class GatherInvalidDefinitionError(Exception):
    pass


class GatherContext:
    def __init__(
        self,
        definitions: dict[str, CoreSchema],
        find_meta_with_keys: set[str] | None,
    ) -> None:
        self.definitions = definitions
        if find_meta_with_keys is None:
            self.meta_with_keys = None
        else:
            self.meta_with_keys = (defaultdict[str, list[CoreSchema]](list), find_meta_with_keys)
        self.inline_def_ref_candidates: dict[str, DefinitionReferenceSchema | None] = {}
        self.recursive_def_refs: set[str] = set()
        self.recursively_seen_refs: set[str] = set()


def gather_meta(schema: CoreSchema, ctx: GatherContext):
    if ctx.meta_with_keys is None:
        return
    res, find_keys = ctx.meta_with_keys
    meta = schema.get('metadata')
    if meta is None:
        return
    for k in find_keys:
        if k in meta:
            res[k].append(schema)


def gather_definition_ref(schema_ref_dict: DefinitionReferenceSchema, ctx: GatherContext):
    schema_ref = schema_ref_dict['schema_ref']

    if schema_ref not in ctx.recursively_seen_refs:
        if schema_ref not in ctx.inline_def_ref_candidates:
            definition = ctx.definitions.get(schema_ref)
            if definition is None:
                raise GatherInvalidDefinitionError(schema_ref)

            ctx.inline_def_ref_candidates[schema_ref] = schema_ref_dict
            ctx.recursively_seen_refs.add(schema_ref)

            gather_schema(definition, ctx)
            if 'serialization' in schema_ref_dict:
                gather_schema(schema_ref_dict['serialization'], ctx)
            gather_meta(schema_ref_dict, ctx)

            ctx.recursively_seen_refs.remove(schema_ref)
        else:
            ctx.inline_def_ref_candidates[schema_ref] = None
    else:
        ctx.inline_def_ref_candidates[schema_ref] = None
        ctx.recursive_def_refs.add(schema_ref)
        for seen_ref in ctx.recursively_seen_refs:
            ctx.inline_def_ref_candidates[seen_ref] = None
            ctx.recursive_def_refs.add(seen_ref)


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

def gather_schemas_for_cleaning(
    schema: CoreSchema,
    definitions: dict[str, CoreSchema],
    find_meta_with_keys: set[str] | None,
) -> GatherResult:
    context = GatherContext(definitions, find_meta_with_keys)
    gather_schema(schema, context)

    return {
        'inlinable_def_refs': context.inline_def_ref_candidates,
        'recursive_refs': context.recursive_def_refs,
        'schemas_with_meta_keys': context.meta_with_keys[0] if context.meta_with_keys is not None else None,
    }
