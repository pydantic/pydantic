# TODO: Should we move WalkAndApply into pydantic_core proper?

from __future__ import annotations

from typing import Callable

from pydantic_core import CoreSchema, CoreSchemaType, core_schema
from typing_extensions import get_args


def consolidate_refs(schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
    """
    This function walks a schema recursively, replacing all but the first occurrence of each ref with
    a definition-ref schema referencing that ref.

    This makes the fundamental assemption that any time two schemas have the same ref, occurrences
    after the first can safely be replaced.

    In most cases, schemas with the same ref should not actually be produced, or should be completely identical.
    However, as an implementation detail, recursive generic models will emit a non-identical schema deeper in the
    tree with a re-used ref, with the intent that that schema gets replaced with a recursive reference once the
    specific generic parametrization to use can be determined.
    """
    refs = set()

    def _replace_refs(s: core_schema.CoreSchema) -> core_schema.CoreSchema:
        # Without the cast, get:
        # pydantic/_internal/_core_utils.py:22: error: Incompatible types in assignment
        # (expression has type "object", variable has type "Optional[str]")  [assignment]
        ref: str | None = s.get('ref')  # type: ignore[assignment]
        if ref:
            if ref in refs:
                return {'type': 'definition-ref', 'schema_ref': ref}
            refs.add(ref)
        return s

    schema = WalkAndApply(_replace_refs, apply_before_recurse=True).walk(schema)
    return schema


def define_expected_missing_refs(
    schema: core_schema.CoreSchema, allowed_missing_refs: set[str]
) -> core_schema.CoreSchema:
    refs = set()

    def _record_refs(s: core_schema.CoreSchema) -> core_schema.CoreSchema:
        ref: str | None = s.get('ref')  # type: ignore[assignment]
        if ref:
            refs.add(ref)
        return s

    WalkAndApply(_record_refs).walk(schema)

    expected_missing_refs = allowed_missing_refs.difference(refs)
    if expected_missing_refs:
        definitions: list[core_schema.CoreSchema] = [
            # TODO: Replace this with a (new) CoreSchema that, if present at any level, makes validation fail
            core_schema.none_schema(ref=ref, metadata={'pydantic_debug_missing_ref': True, 'invalid': True})
            for ref in expected_missing_refs
        ]
        return core_schema.definitions_schema(schema, definitions)
    return schema


def collect_invalid_schemas(schema: core_schema.CoreSchema) -> list[core_schema.CoreSchema]:
    invalid_schemas: list[core_schema.CoreSchema] = []

    def _is_schema_valid(s: core_schema.CoreSchema) -> core_schema.CoreSchema:
        if s.get('metadata', {}).get('invalid'):
            invalid_schemas.append(s)
        return s

    WalkAndApply(_is_schema_valid).walk(schema)
    return invalid_schemas


class WalkAndApply:
    def __init__(
        self, f: Callable[[core_schema.CoreSchema], core_schema.CoreSchema], apply_before_recurse: bool = True
    ):
        self.f = f

        self.apply_before_recurse = apply_before_recurse

        self._schema_type_to_method = self._build_schema_type_to_method()

    def _build_schema_type_to_method(self) -> dict[CoreSchemaType, Callable[[CoreSchema], CoreSchema]]:
        mapping: dict[CoreSchemaType, Callable[[CoreSchema], CoreSchema]] = {}
        for key in get_args(CoreSchemaType):
            method_name = f"handle_{key.replace('-', '_')}_schema"
            mapping[key] = getattr(self, method_name, self._handle_other_schemas)
        return mapping

    def walk(self, schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
        return self._walk(schema)

    def _walk(self, schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
        schema = schema.copy()
        if self.apply_before_recurse:
            schema = self.f(schema)
        method = self._schema_type_to_method[schema['type']]
        schema = method(schema)
        if not self.apply_before_recurse:
            schema = self.f(schema)
        return schema

    def _handle_other_schemas(self, schema: core_schema.CoreSchema) -> core_schema.CoreSchema:
        if 'schema' in schema:
            schema['schema'] = self._walk(schema['schema'])  # type: ignore
        return schema

    def handle_definitions_schema(self, schema: core_schema.DefinitionsSchema) -> CoreSchema:
        new_definitions = []
        for definition in schema['definitions']:
            updated_definition = self._walk(definition)
            if 'ref' in updated_definition:
                # If the updated definition schema doesn't have a 'ref', it shouldn't go in the definitions
                # This is most likely to happen due to replacing something with a definition reference, in
                # which case it should certainly not go in the definitions list
                new_definitions.append(updated_definition)
        new_inner_schema = self._walk(schema['schema'])

        if not new_definitions and len(schema) == 3:
            # This means we'd be returning a "trivial" definitions schema that just wrapped the inner schema
            return new_inner_schema

        new_schema = schema.copy()
        new_schema['schema'] = new_inner_schema
        new_schema['definitions'] = new_definitions
        return new_schema

    def handle_list_schema(self, schema: core_schema.ListSchema) -> CoreSchema:
        if 'items_schema' in schema:
            schema['items_schema'] = self._walk(schema['items_schema'])
        return schema

    def handle_set_schema(self, schema: core_schema.SetSchema) -> CoreSchema:
        if 'items_schema' in schema:
            schema['items_schema'] = self._walk(schema['items_schema'])
        return schema

    def handle_frozenset_schema(self, schema: core_schema.FrozenSetSchema) -> CoreSchema:
        if 'items_schema' in schema:
            schema['items_schema'] = self._walk(schema['items_schema'])
        return schema

    def handle_generator_schema(self, schema: core_schema.GeneratorSchema) -> CoreSchema:
        if 'items_schema' in schema:
            schema['items_schema'] = self._walk(schema['items_schema'])
        return schema

    def handle_tuple_schema(
        self, schema: core_schema.TupleVariableSchema | core_schema.TuplePositionalSchema
    ) -> CoreSchema:
        if 'mode' not in schema or schema['mode'] == 'variable':
            if 'items_schema' in schema:
                # Could drop the # type: ignore on the next line if we made 'mode' required in TupleVariableSchema
                schema['items_schema'] = self._walk(schema['items_schema'])
        elif schema['mode'] == 'positional':
            schema['items_schema'] = [self._walk(v) for v in schema['items_schema']]
            if 'extra_schema' in schema:
                schema['extra_schema'] = self._walk(schema['extra_schema'])
        else:
            raise ValueError(f"Unknown tuple mode: {schema['mode']}")
        return schema

    def handle_dict_schema(self, schema: core_schema.DictSchema) -> CoreSchema:
        if 'keys_schema' in schema:
            schema['keys_schema'] = self._walk(schema['keys_schema'])
        if 'values_schema' in schema:
            schema['values_schema'] = self._walk(schema['values_schema'])
        return schema

    def handle_function_schema(
        self, schema: core_schema.FunctionSchema | core_schema.FunctionPlainSchema | core_schema.FunctionWrapSchema
    ) -> CoreSchema:
        if schema['mode'] == 'plain':
            return schema
        if 'schema' in schema:
            schema['schema'] = self._walk(schema['schema'])
        return schema

    def handle_union_schema(self, schema: core_schema.UnionSchema) -> CoreSchema:
        schema['choices'] = [self._walk(v) for v in schema['choices']]
        return schema

    def handle_tagged_union_schema(self, schema: core_schema.TaggedUnionSchema) -> CoreSchema:
        new_choices: dict[str | int, str | int | CoreSchema] = {}
        for k, v in schema['choices'].items():
            new_choices[k] = v if isinstance(v, (str, int)) else self._walk(v)
        schema['choices'] = new_choices
        return schema

    def handle_chain_schema(self, schema: core_schema.ChainSchema) -> CoreSchema:
        schema['steps'] = [self._walk(v) for v in schema['steps']]
        return schema

    def handle_lax_or_strict_schema(self, schema: core_schema.LaxOrStrictSchema) -> CoreSchema:
        schema['lax_schema'] = self._walk(schema['lax_schema'])
        schema['strict_schema'] = self._walk(schema['strict_schema'])
        return schema

    def handle_typed_dict_schema(self, schema: core_schema.TypedDictSchema) -> CoreSchema:
        if 'extra_validator' in schema:
            schema['extra_validator'] = self._walk(schema['extra_validator'])
        replaced_fields: dict[str, core_schema.TypedDictField] = {}
        for k, v in schema['fields'].items():
            replaced_field = v.copy()
            replaced_field['schema'] = self._walk(v['schema'])
            replaced_fields[k] = replaced_field
        schema['fields'] = replaced_fields
        return schema

    def handle_arguments_schema(self, schema: core_schema.ArgumentsSchema) -> CoreSchema:
        replaced_arguments_schema = []
        for param in schema['arguments_schema']:
            replaced_param = param.copy()
            replaced_param['schema'] = self._walk(param['schema'])
            replaced_arguments_schema.append(replaced_param)
        schema['arguments_schema'] = replaced_arguments_schema
        if 'var_args_schema' in schema:
            schema['var_args_schema'] = self._walk(schema['var_args_schema'])
        if 'var_kwargs_schema' in schema:
            schema['var_kwargs_schema'] = self._walk(schema['var_kwargs_schema'])
        return schema

    def handle_call_schema(self, schema: core_schema.CallSchema) -> CoreSchema:
        schema['arguments_schema'] = self._walk(schema['arguments_schema'])
        if 'return_schema' in schema:
            schema['return_schema'] = self._walk(schema['return_schema'])
        return schema
