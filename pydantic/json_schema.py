"""
Super annoying thing: changing the default value of a field means it can't use the same schema as a $ref...
In particular, a default value of None for a required field means it can't be a $ref.

I guess this means I have to figure out how to implement optional in a better way...?
"""
from __future__ import annotations

import re
import warnings
from dataclasses import asdict, dataclass, is_dataclass, replace
from enum import Enum
from functools import cached_property
from types import EllipsisType
from typing import Any, Callable, Dict, cast

from pydantic_core import CoreSchema, CoreSchemaType, core_schema
from pydantic_core.core_schema import TypedDictField
from typing_extensions import TypeGuard

from pydantic._internal._typing_extra import all_literal_values, is_namedtuple
from pydantic.json import pydantic_encoder

JsonSchemaValue = Dict[str, Any]
JsonValue = Dict[str, Any]

default_ref_template = '#/definitions/{model}'

_JSON_SCHEMA_OVERRIDE_CORE_SCHEMA_FIELD = 'pydantic_json_schema_override_core_schema'
_JSON_SCHEMA_EXTRA_FIELD = 'pydantic_json_schema_extra'
_JSON_SCHEMA_SOURCE_CLASS_NAME_FIELD = 'pydantic_json_schema_source_class'


def build_core_metadata_for_json_schema(
    extra: JsonSchemaExtra | None | EllipsisType = ...,
    override_core_schema: CoreSchema | None | EllipsisType = ...,
    source_class: type[Any] | None | EllipsisType = ...,
    old_metadata: Any | None = None,
) -> Any:
    if not isinstance(old_metadata, (dict, type(None))):
        warnings.warn('CoreSchema metadata should be a dict or None; cannot update with json schema info.', UserWarning)
        return old_metadata

    metadata: dict[Any, Any] = {} if old_metadata is None else old_metadata.copy()

    if extra is not ...:
        metadata[_JSON_SCHEMA_EXTRA_FIELD] = extra

    if override_core_schema is not ...:
        metadata[_JSON_SCHEMA_OVERRIDE_CORE_SCHEMA_FIELD] = override_core_schema

    if source_class is not ...:
        metadata[_JSON_SCHEMA_SOURCE_CLASS_NAME_FIELD] = source_class

    return metadata


def get_core_metadata_json_schema_extra(metadata: Any) -> JsonSchemaExtra | None:
    if not isinstance(metadata, dict):
        return None
    return metadata.get(_JSON_SCHEMA_EXTRA_FIELD)


def get_core_metadata_json_schema_override_core_schema(metadata: Any) -> CoreSchema | None:
    if not isinstance(metadata, dict):
        return None
    return metadata.get(_JSON_SCHEMA_OVERRIDE_CORE_SCHEMA_FIELD)


def get_core_metadata_json_schema_source_class(metadata: Any) -> type[Any] | None:
    if not isinstance(metadata, dict):
        return None
    return metadata.get(_JSON_SCHEMA_SOURCE_CLASS_NAME_FIELD)


@dataclass
class JsonSchemaExtra:
    # see https://json-schema.org/understanding-json-schema/reference/generic.html

    title: str | None = None
    description: str | None = None
    examples: list[JsonValue] | None = None

    # 'default', which is included with these fields in the JsonSchema docs, is handled by CoreSchema
    deprecated: bool | None = None
    read_only: bool | None = None
    write_only: bool | None = None

    comment: str | None = None

    # extra_updates is a catch all for arbitrary data you want to add to the schema,
    # as a simpler version of modify_schema
    extra_updates: dict[str, Any] | None = None

    # Note: modify_schema is called after the schema has been updated based on the contents of all other fields
    modify_schema: Callable[[JsonSchemaValue], JsonSchemaValue] | None = None

    @classmethod
    def merge(cls, base: JsonSchemaExtra | None, overrides: JsonSchemaExtra | None) -> JsonSchemaExtra | None:
        if base is None:
            return overrides
        if overrides is None:
            return base
        return base.with_updates(overrides)

    def with_updates(self, other: JsonSchemaExtra) -> JsonSchemaExtra:
        changes = {k: v for k, v in asdict(other).items() if v is not None}
        return replace(self, **changes)

    def update_json_schema(self, schema: JsonSchemaValue) -> JsonSchemaValue:
        if self.title is not None:
            schema['title'] = self.title
        if self.description is not None:
            schema['description'] = self.description
        if self.examples is not None:
            schema['examples'] = self.examples
        if self.deprecated is not None:
            schema['deprecated'] = self.deprecated
        if self.read_only is not None:
            schema['readOnly'] = self.read_only
        if self.write_only is not None:
            schema['writeOnly'] = self.write_only
        if self.comment is not None:
            schema['$comment'] = self.comment
        if self.extra_updates is not None:
            schema.update(self.extra_updates)
        if self.modify_schema is not None:
            schema = self.modify_schema(schema)
        return schema


def _get_json_refs(json_schema: JsonSchemaValue) -> set[str]:
    json_refs = set()

    def _add_json_refs(schema: JsonSchemaValue) -> None:
        if isinstance(schema, dict):
            if '$ref' in schema:
                json_refs.add(schema['$ref'])
            for v in schema.values():
                _add_json_refs(v)
        elif isinstance(schema, list):
            for v in schema:
                _add_json_refs(v)

    _add_json_refs(json_schema)
    return json_refs


class InvalidForJsonSchema(ValueError):
    pass


# TODO: Probably want a public API for using a subclass of this so users can override their schema generation
class GenerateJsonSchema:
    def __init__(self, by_alias: bool = True, ref_template: str = default_ref_template, strict: bool = True):
        self.by_alias = by_alias
        self.ref_template = ref_template
        self.strict = strict  # if True, prefer the strict branch of LaxOrStrictSchema

        self.definitions: dict[str, JsonSchemaValue] = {}

        # There are three types of references:
        #   1. core_schema "ref" values; these are not exposed as part of the JSON schema
        #       * these might look like the fully qualified path of a model, its id, or something similar
        #       * I will use the term "core_ref" for these
        #   2. keys of the "definitions" object that will eventually go into the JSON schema
        #       * by default, these look like "MyModel", though may change in the presence of collisions
        #       * eventually, we may want to make it easier to modify the way these names are generated
        #       * I will use the term "defs_ref" for these
        #   3. the values corresponding to the "$ref" key in the schema
        #       * By default, these look like "#/definitions/MyModel", as in {"$ref": "#/definitions/MyModel"}
        #       * I will use the term "json_ref" for these
        self.core_to_json_refs: dict[str, str] = {}
        self.json_to_core_refs: dict[str, str] = {}
        self.json_to_defs_refs: dict[str, str] = {}

    @cached_property
    def _schema_type_to_method(self) -> dict[CoreSchemaType, Callable[[CoreSchema], JsonSchemaValue]]:
        mapping: dict[CoreSchemaType, Callable[[CoreSchema], JsonSchemaValue]] = {}
        for key in all_literal_values(CoreSchemaType):  # type: ignore[arg-type]
            method_name = f"{key.replace('-', '_')}_schema"
            try:
                mapping[key] = getattr(self, method_name)
            except AttributeError as e:
                raise TypeError(
                    f'No method for generating JsonSchema for core_schema.type={key!r} '
                    f'(expected: {type(self).__name__}.{method_name})'
                ) from e
        return mapping

    def generate(self, schema: CoreSchema) -> JsonSchemaValue:
        json_schema = self._generate(schema)

        # Remove the top-level $ref if present; note that the _generate method already ensures there are no sibling keys
        if '$ref' in json_schema:
            json_schema_ref = json_schema['$ref']
            json_schema = self._get_referenced_schema(json_schema_ref)

        # Remove any definitions that, thanks to $ref-substitution, are no longer present
        # This should only _possibly_ apply to the root model. It might be safe to remove this logic,
        # but I'm keeping it for now
        remaining_json_refs = _get_json_refs(json_schema)
        all_json_refs = list(self.json_to_defs_refs.keys())
        for k in all_json_refs:
            if k not in remaining_json_refs:
                del self.definitions[self.json_to_defs_refs[k]]

        if self.definitions:
            json_schema['definitions'] = self.definitions

        return json_schema

    def _generate(self, schema: CoreSchema | TypedDictField) -> JsonSchemaValue:
        # TODO: Should make sure model results are cached appropriately on the respective classes
        # Try to load from the "cache":
        if 'ref' in schema:
            core_ref: str = schema['ref']  # type: ignore[typeddict-item]
            if core_ref in self.core_to_json_refs:
                return self._ref_json_schema(self.core_to_json_refs[core_ref])

        # Check for an override core schema; if it exists, return it
        override_core_schema = get_core_metadata_json_schema_override_core_schema(schema.get('metadata'))
        if override_core_schema is not None:
            json_schema = self._generate(override_core_schema)
        else:
            # Handle the core-schema-type-specific bits of the schema generation:
            if _is_typed_dict_field(schema):
                json_schema = self.typed_dict_field_schema(schema)
            elif _is_core_schema(schema):  # Ideally we wouldn't need this redundant typeguard..
                generate_for_schema_type = self._schema_type_to_method[schema['type']]
                json_schema = generate_for_schema_type(schema)

            # Handle the "generic" bits of the schema generation:
            extra = get_core_metadata_json_schema_extra(schema.get('metadata'))
            if extra is not None:
                if '$ref' in json_schema and schema.get('type') == 'model':
                    # This is a hack relating to the fact that the typed_dict_schema is where the ref is set
                    extra.update_json_schema(self._get_referenced_schema(json_schema['$ref']))
                else:
                    extra.update_json_schema(json_schema)

            # Resolve issues caused by sibling keys to a top-level $ref:
            self._handle_ref_overrides(json_schema)

        # Populate the "cache"
        if 'ref' in schema:
            core_ref = schema['ref']  # type: ignore[typeddict-item]
            json_ref = self.get_json_ref(core_ref)
            self.definitions[json_ref] = json_schema
            json_schema = self._ref_json_schema(json_ref)

        return json_schema

    def _handle_ref_overrides(self, json_schema: JsonSchemaValue) -> JsonSchemaValue:
        """
        It is not valid for a schema with a top-level $ref to have sibling keys.

        During our own schema generation, we treat sibling keys as overrides to the referenced schema,
        but this is not how the official JSON schema spec works.

        Because of this, we first remove any sibling keys that are redundant with the referenced schema, then if
        any remain, we transform the schema from a top-level '$ref' to use allOf to move the $ref out of the top level.
        (See bottom of https://swagger.io/docs/specification/using-ref/ for a reference about this behavior)
        """
        if '$ref' in json_schema:
            # prevent modifications to the input; this copy may be safe to drop if there is significant overhead
            json_schema = json_schema.copy()

            json_schema_ref = json_schema['$ref']
            referenced_json_schema = self._get_referenced_schema(json_schema_ref)
            for k, v in json_schema.items():
                if k == '$ref':
                    continue
                if k in referenced_json_schema and referenced_json_schema[k] == v:
                    del json_schema[k]  # redundant key
            if len(json_schema) > 1:
                # There is a remaining "override" key, so we need to move $ref out of the top level
                json_schema_ref = json_schema['$ref']
                del json_schema['$ref']
                assert 'allOf' not in json_schema  # this should never happen, but just in case
                json_schema['allOf'] = [{'$ref': json_schema_ref}]

        return json_schema

    def get_json_ref(self, core_ref: str) -> str:
        """
        Note: we may want to make it easy to override this behavior; I'm not sure if the specific values matter
        At the very least, someone may not want to leak the structure of their codebase via module names
        """
        # try reading from the "cache"
        maybe_json_ref = self.core_to_json_refs.get(core_ref)
        if maybe_json_ref is not None:
            return maybe_json_ref

        # TODO: Note: core_refs are not _currently_ guaranteed to be different for different models,
        #  we should change this; ideally, make core_ref <id(cls)>:<cls.__name__>
        json_ref = re.sub(r'[^a-zA-Z0-9.\-_]', '_', core_ref.split('.')[-1])
        if self.json_to_core_refs.get(json_ref, core_ref) != core_ref:
            json_ref = re.sub(r'[^a-zA-Z0-9.\-_]', '_', core_ref)
        while self.json_to_core_refs.get(json_ref, core_ref) != core_ref:
            # Hitting a collision; add trailing `_` until we don't hit a collision
            json_ref += '_'
            # TODO: I think a better way to do this is to error if/when there is a conflict, and add a way to explicitly
            #   specify what the defs_ref should be for the model. Likely on JsonSchemaExtra...
            # TODO: Note, if we load cached schemas from other models, may need to ensure refs are consistent
            #   Proposal: the generator class should be a part of the cache key, and whatever is set on the "root"
            #   schema generation will be used all the way down. If you want to modify the schema generation for
            #   an individual model only, without affecting how other schemas are generated, that should be done
            #   via the __pydantic_json_schema_extra__ method -- specifically, setting JsonSchemaExtra.modify_schema
            #   Note: If we use the class method for generating the schema, we could provide a way to change the
            #   generator class for child models, but I'm not sure that would be a good idea

        # populate the "caches"
        self.core_to_json_refs[core_ref] = json_ref
        self.json_to_core_refs[json_ref] = core_ref
        return json_ref

    def any_schema(self, schema: core_schema.AnySchema) -> JsonSchemaValue:
        return {}

    def none_schema(self, schema: core_schema.NoneSchema) -> JsonSchemaValue:
        return {'type': 'null'}

    def bool_schema(self, schema: core_schema.BoolSchema) -> JsonSchemaValue:
        return {'type': 'boolean'}

    def int_schema(self, schema: core_schema.IntSchema) -> JsonSchemaValue:
        json_schema = {'type': 'integer'}
        update_with_validations(json_schema, schema, ValidationsMapping.numeric)
        return json_schema

    def float_schema(self, schema: core_schema.FloatSchema) -> JsonSchemaValue:
        json_schema = {'type': 'number'}
        update_with_validations(json_schema, schema, ValidationsMapping.numeric)
        return json_schema

    def str_schema(self, schema: core_schema.StringSchema) -> JsonSchemaValue:
        json_schema = {'type': 'string'}
        update_with_validations(json_schema, schema, ValidationsMapping.string)
        return json_schema

    def bytes_schema(self, schema: core_schema.BytesSchema) -> JsonSchemaValue:
        json_schema = {'type': 'string', 'format': 'binary'}
        update_with_validations(json_schema, schema, ValidationsMapping.bytes)
        return json_schema

    def date_schema(self, schema: core_schema.DateSchema) -> JsonSchemaValue:
        json_schema = {'type': 'string', 'format': 'date'}
        update_with_validations(json_schema, schema, ValidationsMapping.date)
        return json_schema

    def time_schema(self, schema: core_schema.TimeSchema) -> JsonSchemaValue:
        return {'type': 'string', 'format': 'time'}

    def datetime_schema(self, schema: core_schema.DatetimeSchema) -> JsonSchemaValue:
        return {'type': 'string', 'format': 'date-time'}

    def timedelta_schema(self, schema: core_schema.TimedeltaSchema) -> JsonSchemaValue:
        # It's weird that this schema has 'type': 'number' but also specifies a 'format'.
        # Relevant issue: https://github.com/pydantic/pydantic/issues/5034
        # TODO: Probably should just change this to str (look at readme intro for speeddate)
        return {'type': 'number', 'format': 'time-delta'}

    def literal_schema(self, schema: core_schema.LiteralSchema) -> JsonSchemaValue:
        expected = list(schema['expected'])
        if len(expected) == 1:
            return {'const': expected[0]}
        else:
            return {'enum': expected}

    def is_instance_schema(self, schema: core_schema.IsInstanceSchema) -> JsonSchemaValue:
        raise InvalidForJsonSchema('Cannot generate a JsonSchema for core_schema.IsInstanceSchema')

    def is_subclass_schema(self, schema: core_schema.IsSubclassSchema) -> JsonSchemaValue:
        # raise InvalidForJsonSchema('Cannot generate a JsonSchema for core_schema.IsSubclassSchema')
        return {}  # for compatibility with V1 -- is this the right thing to do?

    def callable_schema(self, schema: core_schema.CallableSchema) -> JsonSchemaValue:
        raise InvalidForJsonSchema('Cannot generate a JsonSchema for core_schema.CallableSchema')

    def list_schema(self, schema: core_schema.ListSchema) -> JsonSchemaValue:
        items_schema = {} if 'items_schema' not in schema else self._generate(schema['items_schema'])
        json_schema = {'type': 'array', 'items': items_schema}
        update_with_validations(json_schema, schema, ValidationsMapping.array)
        return json_schema

    def tuple_schema(
        self, schema: core_schema.TupleVariableSchema | core_schema.TuplePositionalSchema
    ) -> JsonSchemaValue:
        json_schema: JsonSchemaValue = {'type': 'array'}

        if 'mode' not in schema:
            json_schema['items'] = {}

        elif schema['mode'] == 'variable':
            if 'items_schema' in schema:
                json_schema['items'] = self._generate(schema['items_schema'])
            update_with_validations(json_schema, schema, ValidationsMapping.array)

        elif schema['mode'] == 'positional':
            json_schema['minItems'] = len(schema['items_schema'])
            prefixItems = [self._generate(item) for item in schema['items_schema']]
            if prefixItems:
                json_schema['prefixItems'] = prefixItems
            if 'extra_schema' in schema:
                json_schema['items'] = self._generate(schema['extra_schema'])
            else:
                json_schema['maxItems'] = len(schema['items_schema'])

        else:
            raise ValueError(f'Unknown tuple schema mode: {schema["mode"]}')

        update_with_validations(json_schema, schema, ValidationsMapping.array)
        return json_schema

    def set_schema(self, schema: core_schema.SetSchema) -> JsonSchemaValue:
        return self._common_set_schema(schema)

    def frozenset_schema(self, schema: core_schema.FrozenSetSchema) -> JsonSchemaValue:
        return self._common_set_schema(schema)

    def _common_set_schema(self, schema: core_schema.SetSchema | core_schema.FrozenSetSchema) -> JsonSchemaValue:
        items_schema = {} if 'items_schema' not in schema else self._generate(schema['items_schema'])
        json_schema = {'type': 'array', 'uniqueItems': True, 'items': items_schema}
        update_with_validations(json_schema, schema, ValidationsMapping.array)
        return json_schema

    def generator_schema(self, schema: core_schema.GeneratorSchema) -> JsonSchemaValue:
        items_schema = {} if 'items_schema' not in schema else self._generate(schema['items_schema'])
        json_schema = {'type': 'array', 'items': items_schema}
        update_with_validations(json_schema, schema, ValidationsMapping.array)
        return json_schema

    def dict_schema(self, schema: core_schema.DictSchema) -> JsonSchemaValue:
        values_schema = self._generate(schema['values_schema']).copy() if 'values_schema' in schema else {}
        values_schema.pop('title', None)  # don't give a title to the additionalProperties

        json_schema: JsonSchemaValue = {'type': 'object'}
        if values_schema:  # don't add additionalProperties if it's empty
            json_schema['additionalProperties'] = values_schema

        update_with_validations(json_schema, schema, ValidationsMapping.object)
        return json_schema

    def function_schema(self, schema: core_schema.FunctionSchema) -> JsonSchemaValue:
        # I'm not sure if this might need to be different if the function's mode is 'before'
        if schema['mode'] == 'plain':
            # Note: If this behavior is not desirable, it might make sense to add an override_core_schema
            # for json schema generation wherever we are generating 'plain' function schemas
            raise InvalidForJsonSchema(f'Cannot generate a JsonSchema for function {schema["function"]}')
        else:
            # 'after', 'before', and 'wrap' functions all have a required 'schema' field
            return self._generate(schema['schema'])

    def default_schema(self, schema: core_schema.WithDefaultSchema) -> JsonSchemaValue:
        if 'default' in schema:
            default = encode_default(schema['default'])
        elif 'default_factory' in schema:
            default = encode_default(schema['default_factory']())
        else:
            raise ValueError('`schema` has neither default nor default_factory')

        json_schema = self._generate(schema['schema'])
        if '$ref' in json_schema:
            # Since reference schemas do not support child keys, we wrap the reference schema in a single-case anyOf:
            return {'anyOf': [json_schema], 'default': default}
        else:
            json_schema['default'] = default
            return json_schema

    def nullable_schema(self, schema: core_schema.NullableSchema) -> JsonSchemaValue:
        null_schema = {'type': 'null'}
        inner_json_schema = self._generate(schema['schema'])

        if inner_json_schema == null_schema:
            return null_schema
        else:
            # Thanks to the equality check against `null_schema` above, I think 'oneOf' would also be valid here;
            # I'll use 'anyOf' for now, but it could be changed it if it would work better with some external tooling
            return self._get_flattened_anyof([null_schema, inner_json_schema])

    def union_schema(self, schema: core_schema.UnionSchema) -> JsonSchemaValue:
        generated: list[JsonSchemaValue] = []

        choices = schema['choices']
        for s in choices:
            try:
                generated.append(self._generate(s))
            except InvalidForJsonSchema:
                pass
        if len(generated) == 1:
            return generated[0]
        return self._get_flattened_anyof(generated)

    def tagged_union_schema(self, schema: core_schema.TaggedUnionSchema) -> JsonSchemaValue:
        generated: dict[str, JsonSchemaValue] = {}
        for k, v in schema['choices'].items():
            if not isinstance(v, str):
                try:
                    generated[k] = self._generate(v).copy()
                except InvalidForJsonSchema:
                    pass
        json_schema: JsonSchemaValue = {'oneOf': list(generated.values())}

        # This reflects the v1 behavior, but we may want to only include the discriminator based on dialect / etc.
        if 'discriminator' in schema and isinstance(schema['discriminator'], str):
            json_schema['discriminator'] = {
                # TODO: Need to handle the case where the discriminator field has an alias
                #   Note: Weird things would happen if the discriminator had a different alias for different choices
                #   (This wouldn't make sense in OpenAPI)
                # TODO: Probably want to create some convenience functions for resolving aliases,
                #   and/or bake them more fully into the core schema.
                # TODO: Confirm with samuel:
                #   Does the current CoreSchema stuff enable us to handle TaggedUnions with aliases properly?
                'propertyName': schema['discriminator'],
                'mapping': {k: v.get('$ref', v) for k, v in generated.items()},
            }

        return json_schema

    def chain_schema(self, schema: core_schema.ChainSchema) -> JsonSchemaValue:
        try:
            # Note: If we wanted to generate a schema for the _serialization_, would want to use the _last_ step:
            return self._generate(schema['steps'][0])
        except IndexError as e:
            raise ValueError('Cannot generate a JsonSchema for a zero-step ChainSchema') from e

    def lax_or_strict_schema(self, schema: core_schema.LaxOrStrictSchema) -> JsonSchemaValue:
        # TODO: We might need to use more complex logic than just defaulting to an attribute set on this class.
        #   In particular, we might need to read the value off of another config object, I'm not sure what though yet
        use_strict = schema.get('strict', self.strict)
        if use_strict:
            return self._generate(schema['strict_schema'])
        else:
            return self._generate(schema['lax_schema'])

    def typed_dict_schema(self, schema: core_schema.TypedDictSchema) -> JsonSchemaValue:
        properties: dict[str, JsonSchemaValue] = {}
        required: list[str] = []
        for name, field in schema['fields'].items():
            # TODO: once more logic exists for alias handling, try to share it with _get_argument_name
            if self.by_alias:
                alias = field.get('validation_alias', name)
                if isinstance(alias, str):
                    name = alias
                else:
                    # TODO: What should be done in this case?
                    #   Maybe tell users to override this method if they want custom behavior here?
                    #       (If populate by name is false)
                    pass
            field_json_schema = self._generate(field).copy()
            if _should_set_field_title(field):
                title = self._title_from_name(name)
                field_json_schema['title'] = title
            field_json_schema = self._handle_ref_overrides(field_json_schema)
            properties[name] = field_json_schema
            if field['required']:
                required.append(name)

        json_schema = {'type': 'object', 'properties': properties}
        if required:
            json_schema['required'] = required
        return json_schema

    def typed_dict_field_schema(self, schema: core_schema.TypedDictField) -> JsonSchemaValue:
        json_schema = self._generate(schema['schema'])

        return json_schema

    def _get_referenced_schema(self, json_ref: str) -> JsonSchemaValue:
        return self.definitions[self.json_to_defs_refs[json_ref]]

    def model_schema(self, schema: core_schema.ModelSchema) -> JsonSchemaValue:
        # TODO: -- Try to pull the schema off the schema.cls, and use the method to grab the value
        #   Maybe: need to add cache keys related to parent class; maybe want to

        # TODO: Note the relationship between this and TypedDictSchema --
        #   should we do something similar with LiteralSchema and a possibly-new EnumSchema?
        #   Main reason not to: Enums aren't special in C API, so maybe not appropriate in pydantic core
        #       However, we can introspect the FunctionSchema to see if it's an enum (or use extra),
        #       and ideally we _should_ put enums into the definitions

        # TODO: try handling Enums via .extra
        json_schema = self._generate(schema['schema'])

        if 'config' in schema and 'title' in schema['config']:
            title = schema['config']['title']
            if '$ref' in json_schema:
                # hack: update the definition from the typed_dict_schema to include the title
                self._get_referenced_schema(json_schema['$ref'])['title'] = title
            else:
                json_schema.setdefault('title', title)
        return json_schema

    def arguments_schema(self, schema: core_schema.ArgumentsSchema) -> JsonSchemaValue:
        arguments = schema['arguments_schema']

        kw_only_arguments = [a for a in arguments if a['mode'] == 'keyword_only']
        kw_or_p_arguments = [a for a in arguments if a['mode'] == 'positional_or_keyword']
        p_only_arguments = [a for a in arguments if a['mode'] == 'positional_only']
        var_args_schema = schema.get('var_args_schema')
        var_kwargs_schema = schema.get('var_kwargs_schema')

        keyword_possible = not p_only_arguments and not var_args_schema
        if keyword_possible:
            return self._kw_arguments_schema(kw_or_p_arguments + kw_only_arguments, var_kwargs_schema)

        positional_possible = not kw_only_arguments and not var_kwargs_schema
        if positional_possible:
            return self._p_arguments_schema(p_only_arguments + kw_or_p_arguments, var_args_schema)

        return {
            'type': 'object',
            'properties': {
                '__args__': self._p_arguments_schema(p_only_arguments, var_args_schema),
                '__kwargs__': self._kw_arguments_schema(kw_or_p_arguments + kw_only_arguments, var_args_schema),
            },
        }

    def _kw_arguments_schema(
        self, arguments: list[core_schema.ArgumentsParameter], var_kwargs_schema: CoreSchema | None
    ) -> JsonSchemaValue:
        properties: dict[str, JsonSchemaValue] = {}
        required: list[str] = []
        for argument in arguments:
            name = self._get_argument_name(argument)
            argument_schema = self._generate(argument['schema']).copy()
            argument_schema['title'] = self._title_from_name(name)
            properties[name] = argument_schema

            if argument['schema']['type'] != 'default':
                # This assumes that if the argument has a default value,
                # the inner schema must be of type WithDefaultSchema.
                # I believe this is true, but I am not 100% sure
                required.append(name)

        json_schema: JsonSchemaValue = {'type': 'object', 'properties': properties}
        if required:
            json_schema['required'] = required

        if var_kwargs_schema:
            additional_properties_schema = self._generate(var_kwargs_schema)
            if additional_properties_schema:
                json_schema['additionalProperties'] = additional_properties_schema
        else:
            json_schema['additionalProperties'] = False
        return json_schema

    def _p_arguments_schema(
        self, arguments: list[core_schema.ArgumentsParameter], var_args_schema: CoreSchema | None
    ) -> JsonSchemaValue:
        prefix_items: list[JsonSchemaValue] = []
        min_items = 0

        for argument in arguments:
            name = self._get_argument_name(argument)

            argument_schema = self._generate(argument['schema']).copy()
            argument_schema['title'] = self._title_from_name(name)
            prefix_items.append(argument_schema)

            if argument['schema']['type'] != 'default':
                # This assumes that if the argument has a default value,
                # the inner schema must be of type WithDefaultSchema.
                # I believe this is true, but I am not 100% sure
                min_items += 1

        json_schema: JsonSchemaValue = {'type': 'array', 'prefixItems': prefix_items}
        if min_items:
            json_schema['minItems'] = min_items

        if var_args_schema:
            items_schema = self._generate(var_args_schema)
            if items_schema:
                json_schema['items'] = items_schema
        else:
            json_schema['maxItems'] = len(prefix_items)

        return json_schema

    def _get_argument_name(self, argument: core_schema.ArgumentsParameter) -> str:
        name = argument['name']
        if self.by_alias:
            # TODO: Need to respect populate_by_name, config, etc.
            alias = argument.get('alias')
            if isinstance(alias, str):
                name = alias
            else:
                pass  # might want to do something else?
        return name

    def _title_from_name(self, name: str) -> str:
        return name.title().replace('_', ' ')

    def call_schema(self, schema: core_schema.CallSchema) -> JsonSchemaValue:
        return self._generate(schema['arguments_schema'])

    def recursive_ref_schema(self, schema: core_schema.RecursiveReferenceSchema) -> JsonSchemaValue:
        json_ref = self.get_json_ref(schema['schema_ref'])
        return self._ref_json_schema(json_ref)

    def _ref_json_schema(self, json_ref: str) -> JsonSchemaValue:
        rendered_template = self.ref_template.format(model=json_ref)
        self.json_to_defs_refs[rendered_template] = json_ref
        return {'$ref': rendered_template}

    def custom_error_schema(self, schema: core_schema.CustomErrorSchema) -> JsonSchemaValue:
        return self._generate(schema['schema'])

    def json_schema(self, schema: core_schema.JsonSchema) -> JsonSchemaValue:
        return {'type': 'string', 'format': 'json-string'}

    def url_schema(self, schema: core_schema.UrlSchema) -> JsonSchemaValue:
        json_schema = {'type': 'string', 'format': 'uri', 'minLength': 1}
        update_with_validations(json_schema, schema, ValidationsMapping.string)
        return json_schema

    def multi_host_url_schema(self, schema: core_schema.MultiHostUrlSchema) -> JsonSchemaValue:
        # Note: 'multi-host-uri' is a custom/pydantic-specific format, not part of the JSON Schema spec
        json_schema = {'type': 'string', 'format': 'multi-host-uri', 'minLength': 1}
        update_with_validations(json_schema, schema, ValidationsMapping.string)
        return json_schema

    @staticmethod
    def _get_flattened_anyof(schemas: list[JsonSchemaValue]) -> JsonSchemaValue:
        members = []
        for schema in schemas:
            if len(schema) == 1 and 'anyOf' in schema:
                members.extend(schema['anyOf'])
            else:
                members.append(schema)
        return {'anyOf': members}


class ValidationsMapping:
    numeric = {
        'multiple_of': 'multipleOf',
        'le': 'maximum',
        'ge': 'minimum',
        'lt': 'exclusiveMaximum',
        'gt': 'exclusiveMinimum',
    }
    bytes = {
        'min_length': 'minLength',
        'max_length': 'maxLength',
    }
    string = {
        'min_length': 'minLength',
        'max_length': 'maxLength',
        'pattern': 'pattern',
    }
    array = {
        'min_length': 'minItems',
        'max_length': 'maxItems',
    }
    object = {
        'min_length': 'minProperties',
        'max_length': 'maxProperties',
    }
    date = {
        'le': 'maximum',
        'ge': 'minimum',
        'lt': 'exclusiveMaximum',
        'gt': 'exclusiveMinimum',
    }


def update_with_validations(json_schema: JsonSchemaValue, core_schema: CoreSchema, mapping: dict[str, str]) -> None:
    for core_key, json_schema_key in mapping.items():
        if core_key in core_schema:
            json_schema[json_schema_key] = core_schema[core_key]  # type: ignore[literal-required]


def encode_default(dft: Any) -> Any:
    from .main import BaseModel

    if isinstance(dft, BaseModel) or is_dataclass(dft):
        dft = cast('dict[str, Any]', pydantic_encoder(dft))

    if isinstance(dft, dict):
        return {encode_default(k): encode_default(v) for k, v in dft.items()}
    elif isinstance(dft, Enum):
        return dft.value
    elif isinstance(dft, (int, float, str)):
        return dft
    elif isinstance(dft, (list, tuple)):
        t = dft.__class__
        seq_args = (encode_default(v) for v in dft)
        return t(*seq_args) if is_namedtuple(t) else t(seq_args)
    elif dft is None:
        return None
    else:
        return pydantic_encoder(dft)


def _is_typed_dict_field(schema: CoreSchema | TypedDictField) -> TypeGuard[TypedDictField]:
    return 'type' not in schema


def _is_core_schema(schema: CoreSchema | TypedDictField) -> TypeGuard[CoreSchema]:
    return 'type' in schema


def _should_set_field_title(schema: CoreSchema | TypedDictField) -> bool:
    override = get_core_metadata_json_schema_override_core_schema(schema.get('metadata'))
    if override:
        return _should_set_field_title(override)

    if _is_typed_dict_field(schema):
        return _should_set_field_title(schema['schema'])

    elif _is_core_schema(schema):
        # TODO: This is probably not handling some schema types it should
        if schema['type'] in {'default', 'nullable', 'model'}:
            return _should_set_field_title(schema['schema'])  # type: ignore[typeddict-item]
        if schema['type'] == 'function' and 'schema' in schema:
            return _should_set_field_title(schema['schema'])  # type: ignore[typeddict-item]
        return not schema.get('ref')  # models, enums should not have titles set

    else:
        raise ValueError(f'Unexpected schema type: {schema}')
