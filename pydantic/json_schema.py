from __future__ import annotations as _annotations

import inspect
import math
import re
import sys
import warnings
from dataclasses import is_dataclass
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Counter,
    Dict,
    Iterable,
    List,
    NewType,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)
from weakref import WeakKeyDictionary

import pydantic_core
from typing_extensions import Literal

from ._internal import _core_metadata, _core_utils, _typing_extra
from .errors import PydanticInvalidForJsonSchema, PydanticUserError

if TYPE_CHECKING:
    from pydantic_core import CoreSchema, CoreSchemaType, core_schema

    from . import ConfigDict
    from ._internal._dataclasses import PydanticDataclass
    from .main import BaseModel

JsonSchemaValue = Dict[str, Any]


def update_json_schema(schema: JsonSchemaValue, updates: dict[str, Any]) -> JsonSchemaValue:
    """
    A convenience function useful for creating `js_modify_function` functions that just set values for some keys.

    TODO: This is basically just a wrapper for dict.update that returns the dict.
        Would it be better to just make this a less-"domain-specific" utility function?
    """
    schema.update(updates)
    return schema


# These are "kind" labels that can be used to control warnings. See `GenerateJsonSchema.render_warning_message`
JsonSchemaWarningKind = Literal['skipped-choice', 'non-serializable-default']


class PydanticJsonSchemaWarning(UserWarning):
    """
    This class is used to emit warnings produced during JSON schema generation.
    See the `GenerateJsonSchema.emit_warning` and `GenerateJsonSchema.render_warning_message`
    methods for more details; these can be overridden to control warning behavior
    """


# ##### JSON Schema Generation #####
DEFAULT_REF_TEMPLATE = '#/$defs/{model}'

# There are three types of references relevant to building JSON schemas:
#   1. core_schema "ref" values; these are not exposed as part of the JSON schema
#       * these might look like the fully qualified path of a model, its id, or something similar
CoreRef = NewType('CoreRef', str)
#   2. keys of the "definitions" object that will eventually go into the JSON schema
#       * by default, these look like "MyModel", though may change in the presence of collisions
#       * eventually, we may want to make it easier to modify the way these names are generated
DefsRef = NewType('DefsRef', str)
#   3. the values corresponding to the "$ref" key in the schema
#       * By default, these look like "#/$defs/MyModel", as in {"$ref": "#/$defs/MyModel"}
JsonRef = NewType('JsonRef', str)


class GenerateJsonSchema:
    # See https://json-schema.org/understanding-json-schema/reference/schema.html#id4 for more info about dialects
    schema_dialect = 'https://json-schema.org/draft/2020-12/schema'

    # `self.render_warning_message` will do nothing if its argument `kind` is in `ignored_warning_kinds`;
    # this value can be modified on subclasses to easily control which warnings are emitted
    ignored_warning_kinds: set[JsonSchemaWarningKind] = {'skipped-choice'}

    def __init__(self, by_alias: bool = True, ref_template: str = DEFAULT_REF_TEMPLATE):
        self.by_alias = by_alias
        self.ref_template = ref_template

        self.core_to_json_refs: dict[CoreRef, JsonRef] = {}
        self.core_to_defs_refs: dict[CoreRef, DefsRef] = {}
        self.defs_to_core_refs: dict[DefsRef, CoreRef] = {}
        self.json_to_defs_refs: dict[JsonRef, DefsRef] = {}

        self.definitions: dict[DefsRef, JsonSchemaValue] = {}

        # When collisions are detected, we choose a non-colliding name
        # during generation, but we also track the colliding tag so that it
        # can be remapped for the first occurrence at the end of the process
        self.collisions: set[DefsRef] = set()
        self.defs_ref_fallbacks: dict[CoreRef, list[DefsRef]] = {}

        self._schema_type_to_method = self.build_schema_type_to_method()

        # This changes to True after generating a schema, to prevent issues caused by accidental re-use
        # of a single instance of a schema generator
        self._used = False

    def build_schema_type_to_method(self) -> dict[CoreSchemaType, Callable[[CoreSchema], JsonSchemaValue]]:
        mapping: dict[CoreSchemaType, Callable[[CoreSchema], JsonSchemaValue]] = {}
        for key in _typing_extra.all_literal_values(pydantic_core.CoreSchemaType):  # type: ignore[arg-type]
            method_name = f"{key.replace('-', '_')}_schema"
            try:
                mapping[key] = getattr(self, method_name)
            except AttributeError as e:
                raise TypeError(
                    f'No method for generating JsonSchema for core_schema.type={key!r} '
                    f'(expected: {type(self).__name__}.{method_name})'
                ) from e
        return mapping

    def generate_definitions(self, schemas: list[CoreSchema]) -> dict[DefsRef, JsonSchemaValue]:
        """
        Given a list of core_schema, generate all JSON schema definitions, and return the generated definitions.
        """
        if self._used:
            raise PydanticUserError(
                'This JSON schema generator has already been used to generate a JSON schema. '
                f'You must create a new instance of {type(self).__name__} to generate a new JSON schema.'
            )
        for schema in schemas:
            self.generate_inner(schema)

        self.resolve_collisions({})

        self._used = True
        return self.definitions

    def generate(self, schema: CoreSchema) -> JsonSchemaValue:
        if self._used:
            raise PydanticUserError(
                'This JSON schema generator has already been used to generate a JSON schema. '
                f'You must create a new instance of {type(self).__name__} to generate a new JSON schema.'
            )

        json_schema = self.generate_inner(schema)
        json_ref_counts = self.get_json_ref_counts(json_schema)

        # Remove the top-level $ref if present; note that the _generate method already ensures there are no sibling keys
        ref = json_schema.get('$ref')
        while ref is not None:  # may need to unpack multiple levels
            ref_json_schema = self.get_schema_from_definitions(JsonRef(ref))
            if json_ref_counts[ref] > 1 or ref_json_schema is None:
                # Keep the ref, but use an allOf to remove the top level $ref
                json_schema = {'allOf': [{'$ref': ref}]}
            else:
                # "Unpack" the ref since this is the only reference
                json_schema = ref_json_schema.copy()  # copy to prevent recursive dict reference
                json_ref_counts[ref] -= 1
            ref = json_schema.get('$ref')

        # Remove any definitions that, thanks to $ref-substitution, are no longer present.
        # I think this should only _possibly_ apply to the root model, though I'm not 100% sure.
        # It might be safe to remove this logic, but I'm keeping it for now
        all_json_refs = list(self.json_to_defs_refs.keys())
        for k in all_json_refs:
            if json_ref_counts[k] < 1:
                del self.definitions[self.json_to_defs_refs[k]]

        json_schema = self.resolve_collisions(json_schema)
        if self.definitions:
            json_schema['$defs'] = self.definitions

        # For now, we will not set the $schema key. However, if desired, this can be easily added by overriding
        # this method and adding the following line after a call to super().generate(schema):
        # json_schema['$schema'] = self.schema_dialect

        self._used = True
        return json_schema

    def generate_inner(
        self, schema: CoreSchema | core_schema.TypedDictField | core_schema.DataclassField
    ) -> JsonSchemaValue:
        # If a schema with the same CoreRef has been handled, just return a reference to it
        # Note that this assumes that it will _never_ be the case that the same CoreRef is used
        # on types that should have different JSON schemas
        if 'ref' in schema:
            core_ref = CoreRef(schema['ref'])  # type: ignore[typeddict-item]
            if core_ref in self.core_to_json_refs:
                return {'$ref': self.core_to_json_refs[core_ref]}

        # Generate the JSON schema, accounting for the json_schema_override and core_schema_override
        metadata_handler = _core_metadata.CoreMetadataHandler(schema)
        js_override = metadata_handler.get_js_override()
        js_cs_override = metadata_handler.get_js_cs_override()

        if js_override is not None:
            json_schema = js_override
        elif js_cs_override is not None:
            # If there is a core schema override, use it to generate the JSON schema
            json_schema = self.generate_inner(js_cs_override)
        else:
            # Generate the core-schema-type-specific bits of the schema generation:
            if _core_utils.is_typed_dict_field(schema):
                json_schema = self.typed_dict_field_schema(schema)
            elif _core_utils.is_dataclass_field(schema):
                json_schema = self.dataclass_field_schema(schema)
            elif _core_utils.is_core_schema(schema):  # Ideally we wouldn't need this redundant typeguard..
                generate_for_schema_type = self._schema_type_to_method[schema['type']]
                json_schema = generate_for_schema_type(schema)
            else:
                raise TypeError(f'Unexpected schema type: schema={schema}')

        # Apply the modify_js function, if present
        schema_to_update: JsonSchemaValue | None = None
        if '$ref' in json_schema and schema.get('type') == 'model':
            # If we have a schema with a $ref, we actually need to update the _referenced_ schema
            schema_to_update = self.get_schema_from_definitions(JsonRef(json_schema['$ref']))
        if schema_to_update is not None:
            # Do an in-place update to schema_to_update, regardless of whether the js_modify_function
            # returns a new dict or modifies the old one
            updated = metadata_handler.apply_js_modify_function(schema_to_update).copy()
            schema_to_update.clear()
            schema_to_update.update(updated)
        else:
            json_schema = metadata_handler.apply_js_modify_function(json_schema)

        # Resolve issues caused by sibling keys next to a top-level $ref (see `handle_ref_overrides` for details)
        json_schema = self.handle_ref_overrides(json_schema)

        # Populate the definitions
        if 'ref' in schema:
            core_ref = CoreRef(schema['ref'])  # type: ignore[typeddict-item]
            defs_ref, ref_json_schema = self.get_cache_defs_ref_schema(core_ref)
            self.definitions[defs_ref] = json_schema
            json_schema = ref_json_schema

        return json_schema

    # ### Schema generation methods
    def any_schema(self, schema: core_schema.AnySchema) -> JsonSchemaValue:
        return {}

    def none_schema(self, schema: core_schema.NoneSchema) -> JsonSchemaValue:
        return {'type': 'null'}

    def bool_schema(self, schema: core_schema.BoolSchema) -> JsonSchemaValue:
        return {'type': 'boolean'}

    def int_schema(self, schema: core_schema.IntSchema) -> JsonSchemaValue:
        json_schema = {'type': 'integer'}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.numeric)
        json_schema = {k: v for k, v in json_schema.items() if v not in {math.inf, -math.inf}}
        return json_schema

    def float_schema(self, schema: core_schema.FloatSchema) -> JsonSchemaValue:
        json_schema = {'type': 'number'}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.numeric)
        json_schema = {k: v for k, v in json_schema.items() if v not in {math.inf, -math.inf}}
        return json_schema

    def str_schema(self, schema: core_schema.StringSchema) -> JsonSchemaValue:
        json_schema = {'type': 'string'}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.string)
        return json_schema

    def bytes_schema(self, schema: core_schema.BytesSchema) -> JsonSchemaValue:
        json_schema = {'type': 'string', 'format': 'binary'}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.bytes)
        return json_schema

    def date_schema(self, schema: core_schema.DateSchema) -> JsonSchemaValue:
        json_schema = {'type': 'string', 'format': 'date'}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.date)
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
        expected = [v.value if isinstance(v, Enum) else v for v in schema['expected']]

        if len(expected) == 1:
            return {'const': expected[0]}
        else:
            return {'enum': expected}

    def is_instance_schema(self, schema: core_schema.IsInstanceSchema) -> JsonSchemaValue:
        return self.handle_invalid_for_json_schema(schema, f'core_schema.IsInstanceSchema ({schema["cls"]})')

    def is_subclass_schema(self, schema: core_schema.IsSubclassSchema) -> JsonSchemaValue:
        return {}  # TODO: This was for compatibility with V1 -- is this the right thing to do?

    def callable_schema(self, schema: core_schema.CallableSchema) -> JsonSchemaValue:
        return self.handle_invalid_for_json_schema(schema, 'core_schema.CallableSchema')

    def list_schema(self, schema: core_schema.ListSchema) -> JsonSchemaValue:
        items_schema = {} if 'items_schema' not in schema else self.generate_inner(schema['items_schema'])
        json_schema = {'type': 'array', 'items': items_schema}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.array)
        return json_schema

    def tuple_positional_schema(self, schema: core_schema.TuplePositionalSchema) -> JsonSchemaValue:
        json_schema: JsonSchemaValue = {'type': 'array'}
        json_schema['minItems'] = len(schema['items_schema'])
        prefixItems = [self.generate_inner(item) for item in schema['items_schema']]
        if prefixItems:
            json_schema['prefixItems'] = prefixItems
        if 'extra_schema' in schema:
            json_schema['items'] = self.generate_inner(schema['extra_schema'])
        else:
            json_schema['maxItems'] = len(schema['items_schema'])
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.array)
        return json_schema

    def tuple_variable_schema(self, schema: core_schema.TupleVariableSchema) -> JsonSchemaValue:
        json_schema: JsonSchemaValue = {'type': 'array', 'items': {}}
        if 'items_schema' in schema:
            json_schema['items'] = self.generate_inner(schema['items_schema'])
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.array)
        return json_schema

    def set_schema(self, schema: core_schema.SetSchema) -> JsonSchemaValue:
        return self._common_set_schema(schema)

    def frozenset_schema(self, schema: core_schema.FrozenSetSchema) -> JsonSchemaValue:
        return self._common_set_schema(schema)

    def _common_set_schema(self, schema: core_schema.SetSchema | core_schema.FrozenSetSchema) -> JsonSchemaValue:
        items_schema = {} if 'items_schema' not in schema else self.generate_inner(schema['items_schema'])
        json_schema = {'type': 'array', 'uniqueItems': True, 'items': items_schema}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.array)
        return json_schema

    def generator_schema(self, schema: core_schema.GeneratorSchema) -> JsonSchemaValue:
        items_schema = {} if 'items_schema' not in schema else self.generate_inner(schema['items_schema'])
        json_schema = {'type': 'array', 'items': items_schema}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.array)
        return json_schema

    def dict_schema(self, schema: core_schema.DictSchema) -> JsonSchemaValue:
        json_schema: JsonSchemaValue = {'type': 'object'}

        keys_schema = self.generate_inner(schema['keys_schema']).copy() if 'keys_schema' in schema else {}
        keys_pattern = keys_schema.pop('pattern', None)

        values_schema = self.generate_inner(schema['values_schema']).copy() if 'values_schema' in schema else {}
        values_schema.pop('title', None)  # don't give a title to the additionalProperties
        if values_schema or keys_pattern is not None:  # don't add additionalProperties if it's empty
            if keys_pattern is None:
                json_schema['additionalProperties'] = values_schema
            else:
                json_schema['patternProperties'] = {keys_pattern: values_schema}

        self.update_with_validations(json_schema, schema, self.ValidationsMapping.object)
        return json_schema

    def _function_schema(
        self,
        schema: _core_utils.AnyFunctionSchema,
    ) -> JsonSchemaValue:
        if _core_utils.is_function_with_inner_schema(schema):
            # I'm not sure if this might need to be different if the function's mode is 'before'
            return self.generate_inner(schema['schema'])
        # function-plain
        return self.handle_invalid_for_json_schema(
            schema, f'core_schema.PlainValidatorFunctionSchema ({schema["function"]})'
        )

    def function_before_schema(self, schema: core_schema.BeforeValidatorFunctionSchema) -> JsonSchemaValue:
        return self._function_schema(schema)

    def function_after_schema(self, schema: core_schema.AfterValidatorFunctionSchema) -> JsonSchemaValue:
        return self._function_schema(schema)

    def function_plain_schema(self, schema: core_schema.PlainValidatorFunctionSchema) -> JsonSchemaValue:
        return self._function_schema(schema)

    def function_wrap_schema(self, schema: core_schema.WrapValidatorFunctionSchema) -> JsonSchemaValue:
        return self._function_schema(schema)

    def default_schema(self, schema: core_schema.WithDefaultSchema) -> JsonSchemaValue:
        json_schema = self.generate_inner(schema['schema'])

        if 'default' in schema:
            default = schema['default']
        elif 'default_factory' in schema:
            default = schema['default_factory']()
        else:
            raise ValueError('`schema` has neither default nor default_factory')

        try:
            encoded_default = self.encode_default(default)
        except pydantic_core.PydanticSerializationError:
            self.emit_warning(
                'non-serializable-default',
                f'Default value {default} is not JSON serializable; excluding default from JSON schema',
            )
            # Return the inner schema, as though there was no default
            return json_schema

        if '$ref' in json_schema:
            # Since reference schemas do not support child keys, we wrap the reference schema in a single-case allOf:
            return {'allOf': [json_schema], 'default': encoded_default}
        else:
            json_schema['default'] = encoded_default
            return json_schema

    def nullable_schema(self, schema: core_schema.NullableSchema) -> JsonSchemaValue:
        null_schema = {'type': 'null'}
        inner_json_schema = self.generate_inner(schema['schema'])

        if inner_json_schema == null_schema:
            return null_schema
        else:
            # Thanks to the equality check against `null_schema` above, I think 'oneOf' would also be valid here;
            # I'll use 'anyOf' for now, but it could be changed it if it would work better with some external tooling
            return self.get_flattened_anyof([inner_json_schema, null_schema])

    def union_schema(self, schema: core_schema.UnionSchema) -> JsonSchemaValue:
        generated: list[JsonSchemaValue] = []

        choices = schema['choices']
        for s in choices:
            try:
                generated.append(self.generate_inner(s))
            except PydanticInvalidForJsonSchema as exc:
                self.emit_warning('skipped-choice', str(exc))
        if len(generated) == 1:
            return generated[0]
        return self.get_flattened_anyof(generated)

    def tagged_union_schema(self, schema: core_schema.TaggedUnionSchema) -> JsonSchemaValue:
        generated: dict[str, JsonSchemaValue] = {}
        for k, v in schema['choices'].items():
            if not isinstance(v, (str, int)):
                try:
                    # Use str(k) since keys must be strings for json; while not technically correct,
                    # it's the closest that can be represented in valid JSON
                    generated[str(k)] = self.generate_inner(v).copy()
                except PydanticInvalidForJsonSchema as exc:
                    self.emit_warning('skipped-choice', str(exc))

        # Populate the schema with any "indirect" references
        for k, v in schema['choices'].items():
            if isinstance(v, (str, int)):
                while isinstance(schema['choices'][v], (str, int)):
                    v = schema['choices'][v]
                if str(v) in generated:
                    # while it might seem unnecessary to check `if str(v) in generated`, a PydanticInvalidForJsonSchema
                    # may have been raised above, which would mean that the schema we want to reference won't be present
                    generated[str(k)] = generated[str(v)]

        one_of_choices = _deduplicate_schemas(generated.values())
        json_schema: JsonSchemaValue = {'oneOf': one_of_choices}

        # This reflects the v1 behavior; TODO: we should make it possible to exclude OpenAPI stuff from the JSON schema
        openapi_discriminator = self._extract_discriminator(schema, one_of_choices)
        if openapi_discriminator is not None:
            json_schema['discriminator'] = {
                'propertyName': openapi_discriminator,
                'mapping': {k: v.get('$ref', v) for k, v in generated.items()},
            }

        return json_schema

    def _extract_discriminator(
        self, schema: core_schema.TaggedUnionSchema, one_of_choices: list[_JsonDict]
    ) -> str | None:
        """
        Extract a compatible OpenAPI discriminator from the schema and one_of choices that end up in the final schema.
        """
        openapi_discriminator: str | None = None
        if 'discriminator' not in schema:
            return None

        if isinstance(schema['discriminator'], str):
            return schema['discriminator']

        if isinstance(schema['discriminator'], list):
            # If the discriminator is a single item list containing a string, that is equivalent to the string case
            if len(schema['discriminator']) == 1 and isinstance(schema['discriminator'][0], str):
                return schema['discriminator'][0]
            # When an alias is used that is different from the field name, the discriminator will be a list of single
            # str lists, one for the attribute and one for the actual alias. The logic here will work even if there is
            # more than one possible attribute, and looks for whether a single alias choice is present as a documented
            # property on all choices. If so, that property will be used as the OpenAPI discriminator.
            for alias_path in schema['discriminator']:
                if not isinstance(alias_path, list):
                    break  # this means that the discriminator is not a list of alias paths
                if len(alias_path) != 1:
                    continue  # this means that the "alias" does not represent a single field
                alias = alias_path[0]
                if not isinstance(alias, str):
                    continue  # this means that the "alias" does not represent a field
                alias_is_present_on_all_choices = True
                for choice in one_of_choices:
                    while '$ref' in choice:
                        assert isinstance(choice['$ref'], str)
                        choice = self.get_schema_from_definitions(JsonRef(choice['$ref'])) or {}
                    properties = choice.get('properties', {})
                    if not isinstance(properties, dict) or alias not in properties:
                        alias_is_present_on_all_choices = False
                        break
                if alias_is_present_on_all_choices:
                    openapi_discriminator = alias
                    break
        return openapi_discriminator

    def chain_schema(self, schema: core_schema.ChainSchema) -> JsonSchemaValue:
        try:
            # Note: If we wanted to generate a schema for the _serialization_, would want to use the _last_ step:
            return self.generate_inner(schema['steps'][0])
        except IndexError as e:
            raise ValueError('Cannot generate a JsonSchema for a zero-step ChainSchema') from e

    def lax_or_strict_schema(self, schema: core_schema.LaxOrStrictSchema) -> JsonSchemaValue:
        """
        LaxOrStrict will use the strict branch for serialization internally,
        unless it was overridden here.
        """
        # TODO: Need to read the default value off of model config or whatever
        use_strict = schema.get('strict', False)  # TODO: replace this default False
        # If your JSON schema fails to generate it is probably
        # because one of the following two branches failed.
        if use_strict:
            return self.generate_inner(schema['strict_schema'])
        else:
            return self.generate_inner(schema['lax_schema'])

    def typed_dict_schema(self, schema: core_schema.TypedDictSchema) -> JsonSchemaValue:
        named_required_fields = [(k, v['required'], v) for k, v in schema['fields'].items()]
        return self._named_required_fields_schema(named_required_fields)

    def _named_required_fields_schema(
        self, named_required_fields: Sequence[tuple[str, bool, core_schema.TypedDictField | core_schema.DataclassField]]
    ) -> JsonSchemaValue:
        properties: dict[str, JsonSchemaValue] = {}
        required_fields: list[str] = []
        for name, required, field in named_required_fields:
            if self.by_alias:
                alias = field.get('validation_alias', name)
                if isinstance(alias, str):
                    name = alias
                elif isinstance(alias, list):
                    for path in alias:
                        if isinstance(path, list) and len(path) == 1 and isinstance(path[0], str):
                            # Use the first valid single-item string path; the code that constructs the alias array
                            # should ensure the first such item is what belongs in the JSON schema
                            name = path[0]
                            break
            field_json_schema = self.generate_inner(field).copy()
            if 'title' not in field_json_schema and self.field_title_should_be_set(field):
                title = self.get_title_from_name(name)
                field_json_schema['title'] = title
            field_json_schema = self.handle_ref_overrides(field_json_schema)
            properties[name] = field_json_schema
            if required:
                required_fields.append(name)

        json_schema = {'type': 'object', 'properties': properties}
        if required_fields:
            json_schema['required'] = required_fields
        return json_schema

    def typed_dict_field_schema(self, schema: core_schema.TypedDictField) -> JsonSchemaValue:
        json_schema = self.generate_inner(schema['schema'])

        return json_schema

    def dataclass_field_schema(self, schema: core_schema.DataclassField) -> JsonSchemaValue:
        json_schema = self.generate_inner(schema['schema'])

        return json_schema

    def model_schema(self, schema: core_schema.ModelSchema) -> JsonSchemaValue:
        # We do not use schema['model'].model_json_schema() because it could lead to inconsistent refs handling, etc.
        json_schema = self.generate_inner(schema['schema'])

        if 'config' in schema:
            title = schema['config'].get('title')
            forbid_additional_properties = schema['config'].get('extra_fields_behavior') == 'forbid'
            json_schema = self._update_class_schema(json_schema, title, forbid_additional_properties)

        return json_schema

    def _update_class_schema(
        self, json_schema: JsonSchemaValue, title: str | None, forbid_additional_properties: bool
    ) -> JsonSchemaValue:
        if '$ref' in json_schema:
            schema_to_update = self.get_schema_from_definitions(JsonRef(json_schema['$ref'])) or json_schema
        else:
            schema_to_update = json_schema

        if title is not None:
            # referenced_schema['title'] = title
            schema_to_update.setdefault('title', title)

        if forbid_additional_properties:
            schema_to_update['additionalProperties'] = False

        return json_schema

    def dataclass_args_schema(self, schema: core_schema.DataclassArgsSchema) -> JsonSchemaValue:
        named_required_fields = [
            (field['name'], field['schema']['type'] != 'default', field) for field in schema['fields']
        ]
        return self._named_required_fields_schema(named_required_fields)

    def dataclass_schema(self, schema: core_schema.DataclassSchema) -> JsonSchemaValue:
        # TODO: Better-share this logic with model_schema
        #   I'd prefer to clean this up _after_ we rework the approach to customizing dataclass JSON schema though

        json_schema = self.generate_inner(schema['schema']).copy()

        cls = schema['cls']
        config: ConfigDict = getattr(cls, '__pydantic_config__', cast('ConfigDict', {}))

        title = config.get('title') or cls.__name__
        forbid_additional_properties = config.get('extra') == 'forbid'
        json_schema = self._update_class_schema(json_schema, title, forbid_additional_properties)

        # Dataclass-specific handling of description
        if is_dataclass(cls) and not hasattr(cls, '__pydantic_validator__'):
            # vanilla dataclass; don't use cls.__doc__ as it will contain the class signature by default
            description = None
        else:
            description = None if cls.__doc__ is None else inspect.cleandoc(cls.__doc__)
        if description:
            json_schema['description'] = description

        return json_schema

    def arguments_schema(self, schema: core_schema.ArgumentsSchema) -> JsonSchemaValue:
        metadata = _core_metadata.CoreMetadataHandler(schema).metadata
        prefer_positional = metadata.get('pydantic_js_prefer_positional_arguments')

        arguments = schema['arguments_schema']
        kw_only_arguments = [a for a in arguments if a.get('mode') == 'keyword_only']
        kw_or_p_arguments = [a for a in arguments if a.get('mode') in {'positional_or_keyword', None}]
        p_only_arguments = [a for a in arguments if a.get('mode') == 'positional_only']
        var_args_schema = schema.get('var_args_schema')
        var_kwargs_schema = schema.get('var_kwargs_schema')

        if prefer_positional:
            positional_possible = not kw_only_arguments and not var_kwargs_schema
            if positional_possible:
                return self.p_arguments_schema(p_only_arguments + kw_or_p_arguments, var_args_schema)

        keyword_possible = not p_only_arguments and not var_args_schema
        if keyword_possible:
            return self.kw_arguments_schema(kw_or_p_arguments + kw_only_arguments, var_kwargs_schema)

        if not prefer_positional:
            positional_possible = not kw_only_arguments and not var_kwargs_schema
            if positional_possible:
                return self.p_arguments_schema(p_only_arguments + kw_or_p_arguments, var_args_schema)

        return {
            'type': 'object',
            'properties': {
                '__args__': self.p_arguments_schema(p_only_arguments, var_args_schema),
                '__kwargs__': self.kw_arguments_schema(kw_or_p_arguments + kw_only_arguments, var_args_schema),
            },
        }

    def kw_arguments_schema(
        self, arguments: list[core_schema.ArgumentsParameter], var_kwargs_schema: CoreSchema | None
    ) -> JsonSchemaValue:
        properties: dict[str, JsonSchemaValue] = {}
        required: list[str] = []
        for argument in arguments:
            name = self.get_argument_name(argument)
            argument_schema = self.generate_inner(argument['schema']).copy()
            argument_schema['title'] = self.get_title_from_name(name)
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
            additional_properties_schema = self.generate_inner(var_kwargs_schema)
            if additional_properties_schema:
                json_schema['additionalProperties'] = additional_properties_schema
        else:
            json_schema['additionalProperties'] = False
        return json_schema

    def p_arguments_schema(
        self, arguments: list[core_schema.ArgumentsParameter], var_args_schema: CoreSchema | None
    ) -> JsonSchemaValue:
        prefix_items: list[JsonSchemaValue] = []
        min_items = 0

        for argument in arguments:
            name = self.get_argument_name(argument)

            argument_schema = self.generate_inner(argument['schema']).copy()
            argument_schema['title'] = self.get_title_from_name(name)
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
            items_schema = self.generate_inner(var_args_schema)
            if items_schema:
                json_schema['items'] = items_schema
        else:
            json_schema['maxItems'] = len(prefix_items)

        return json_schema

    def get_argument_name(self, argument: core_schema.ArgumentsParameter) -> str:
        name = argument['name']
        if self.by_alias:
            alias = argument.get('alias')
            if isinstance(alias, str):
                name = alias
            else:
                pass  # might want to do something else?
        return name

    def call_schema(self, schema: core_schema.CallSchema) -> JsonSchemaValue:
        return self.generate_inner(schema['arguments_schema'])

    def custom_error_schema(self, schema: core_schema.CustomErrorSchema) -> JsonSchemaValue:
        return self.generate_inner(schema['schema'])

    def json_schema(self, schema: core_schema.JsonSchema) -> JsonSchemaValue:
        # TODO: For v1 compatibility, we should probably be using `schema['schema']` to produce the schema.
        #   This is a serialization vs. validation thing; see https://github.com/pydantic/pydantic/issues/5072
        #   -
        #   The behavior below is not currently consistent with the v1 behavior, so should probably be changed.
        #   I think making it work like v1 should be as easy as handling schema['schema'] instead, with the note
        #   that we'll need to make generics work with Json (there is a test for this in test_generics.py).
        return {'type': 'string', 'format': 'json-string'}

    def url_schema(self, schema: core_schema.UrlSchema) -> JsonSchemaValue:
        json_schema = {'type': 'string', 'format': 'uri', 'minLength': 1}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.string)
        return json_schema

    def multi_host_url_schema(self, schema: core_schema.MultiHostUrlSchema) -> JsonSchemaValue:
        # Note: 'multi-host-uri' is a custom/pydantic-specific format, not part of the JSON Schema spec
        json_schema = {'type': 'string', 'format': 'multi-host-uri', 'minLength': 1}
        self.update_with_validations(json_schema, schema, self.ValidationsMapping.string)
        return json_schema

    def definitions_schema(self, schema: core_schema.DefinitionsSchema) -> JsonSchemaValue:
        for definition in schema['definitions']:
            self.generate_inner(definition)
        return self.generate_inner(schema['schema'])

    def definition_ref_schema(self, schema: core_schema.DefinitionReferenceSchema) -> JsonSchemaValue:
        core_ref = CoreRef(schema['schema_ref'])
        defs_ref, ref_json_schema = self.get_cache_defs_ref_schema(core_ref)
        return ref_json_schema

    # ### Utility methods

    def get_title_from_name(self, name: str) -> str:
        return name.title().replace('_', ' ')

    def field_title_should_be_set(
        self, schema: CoreSchema | core_schema.TypedDictField | core_schema.DataclassField
    ) -> bool:
        """
        Returns true if a field with the given schema should have a title set based on the field name.

        Intuitively, we want this to return true for schemas that wouldn't otherwise provide their own title
        (e.g., int, float, str), and false for those that would (e.g., BaseModel subclasses).
        """
        if _core_utils.is_typed_dict_field(schema) or _core_utils.is_dataclass_field(schema):
            return self.field_title_should_be_set(schema['schema'])

        elif _core_utils.is_core_schema(schema):
            if schema.get('ref'):  # things with refs, such as models and enums, should not have titles set
                return False

            js_cs_override = _core_metadata.CoreMetadataHandler(schema).get_js_cs_override()
            if js_cs_override:
                return self.field_title_should_be_set(js_cs_override)

            if schema['type'] in {'default', 'nullable', 'definitions'}:
                return self.field_title_should_be_set(schema['schema'])  # type: ignore[typeddict-item]
            if _core_utils.is_function_with_inner_schema(schema):
                return self.field_title_should_be_set(schema['schema'])
            if schema['type'] == 'definition-ref':
                # Referenced schemas should not have titles set for the same reason
                # schemas with refs should not
                return False
            return True  # anything else should have title set

        else:
            raise TypeError(f'Unexpected schema type: schema={schema}')

    def normalize_name(self, name: str) -> str:
        return re.sub(r'[^a-zA-Z0-9.\-_]', '_', name).replace('.', '__')

    def get_defs_ref(self, core_ref: CoreRef) -> DefsRef:
        """
        Override this method to change the way that definitions keys are generated from a core reference.
        """
        # Split the core ref into "components"; generic origins and arguments are each separate components
        components = re.split(r'([\][,])', core_ref)
        # Remove IDs from each component
        components = [x.split(':')[0] for x in components]
        core_ref_no_id = ''.join(components)
        # Remove everything before the last period from each "component"
        components = [re.sub(r'(?:[^.[\]]+\.)+((?:[^.[\]]+))', r'\1', x) for x in components]
        short_ref = ''.join(components)

        first_choice = DefsRef(self.normalize_name(short_ref))  # name
        second_choice = DefsRef(self.normalize_name(core_ref_no_id))  # module + qualname
        third_choice = DefsRef(self.normalize_name(core_ref))  # module + qualname + id

        # It is important that the generated defs_ref values be such that at least one could not
        # be generated for any other core_ref. Currently, this should be the case because we include
        # the id of the source type in the core_ref, and therefore in the third_choice
        choices = [first_choice, second_choice, third_choice]
        self.defs_ref_fallbacks[core_ref] = choices[1:]

        for choice in choices:
            if self.defs_to_core_refs.get(choice, core_ref) == core_ref:
                return choice
            else:
                self.collisions.add(choice)

        return choices[-1]  # should never get here if the final choice is guaranteed unique

    def resolve_collisions(self, json_schema: JsonSchemaValue) -> JsonSchemaValue:
        """
        This function ensures that any defs_ref's that were involved in collisions
        (due to simplification of the core_ref) get updated, even if they were the
        first occurrence of the colliding defs_ref.

        This is intended to prevent confusion where the type that gets the "shortened"
        ref depends on the order in which the types were visited.
        """
        made_changes = True

        # Note that because the defs ref choices eventually produce values that use the IDs and
        # should _never_ collide, it should not be possible for this while loop to run forever
        while made_changes:
            made_changes = False

            for defs_ref, core_ref in self.defs_to_core_refs.items():
                if defs_ref not in self.collisions:
                    continue

                for choice in self.defs_ref_fallbacks[core_ref]:
                    if choice == defs_ref or choice in self.collisions:
                        continue

                    if self.defs_to_core_refs.get(choice, core_ref) == core_ref:
                        json_schema = self.change_defs_ref(defs_ref, choice, json_schema)
                        made_changes = True
                        break
                    else:
                        self.collisions.add(choice)

                if made_changes:
                    break

        return json_schema

    def change_defs_ref(self, old: DefsRef, new: DefsRef, json_schema: JsonSchemaValue) -> JsonSchemaValue:
        if new == old:
            return json_schema
        core_ref = self.defs_to_core_refs[old]
        old_json_ref = self.core_to_json_refs[core_ref]
        new_json_ref = JsonRef(self.ref_template.format(model=new))

        self.definitions[new] = self.definitions.pop(old)
        self.defs_to_core_refs[new] = self.defs_to_core_refs.pop(old)
        self.json_to_defs_refs[new_json_ref] = self.json_to_defs_refs.pop(old_json_ref)
        self.core_to_defs_refs[core_ref] = new
        self.core_to_json_refs[core_ref] = new_json_ref

        def walk_replace_json_schema_ref(item: Any) -> Any:
            """
            Recursively update the JSON schema to use the new defs_ref.
            """
            if isinstance(item, list):
                return [walk_replace_json_schema_ref(item) for item in item]
            elif isinstance(item, dict):
                ref = item.get('$ref')
                if ref == old_json_ref:
                    item['$ref'] = new_json_ref
                return {k: walk_replace_json_schema_ref(v) for k, v in item.items()}
            else:
                return item

        return walk_replace_json_schema_ref(json_schema)

    def get_cache_defs_ref_schema(self, core_ref: CoreRef) -> tuple[DefsRef, JsonSchemaValue]:
        """
        This method wraps the get_defs_ref method with some cache-lookup/population logic,
        and returns both the produced defs_ref and the JSON schema that will refer to the right definition.
        """
        maybe_defs_ref = self.core_to_defs_refs.get(core_ref)
        if maybe_defs_ref is not None:
            json_ref = self.core_to_json_refs[core_ref]
            return maybe_defs_ref, {'$ref': json_ref}

        defs_ref = self.get_defs_ref(core_ref)

        # populate the ref translation mappings
        self.core_to_defs_refs[core_ref] = defs_ref
        self.defs_to_core_refs[defs_ref] = core_ref

        json_ref = JsonRef(self.ref_template.format(model=defs_ref))
        self.core_to_json_refs[core_ref] = json_ref
        self.json_to_defs_refs[json_ref] = defs_ref
        ref_json_schema = {'$ref': json_ref}
        return defs_ref, ref_json_schema

    def handle_ref_overrides(self, json_schema: JsonSchemaValue) -> JsonSchemaValue:
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

            referenced_json_schema = self.get_schema_from_definitions(JsonRef(json_schema['$ref']))
            if referenced_json_schema is None:
                # This can happen when building schemas for models with not-yet-defined references.
                # It may be a good idea to do a recursive pass at the end of the generation to remove
                # any redundant override keys.
                if len(json_schema) > 1:
                    # Make it an allOf to at least resolve the sibling keys issue
                    json_schema = json_schema.copy()
                    json_schema.setdefault('allOf', [])
                    json_schema['allOf'].append({'$ref': json_schema['$ref']})
                    del json_schema['$ref']

                return json_schema
            for k, v in list(json_schema.items()):
                if k == '$ref':
                    continue
                if k in referenced_json_schema and referenced_json_schema[k] == v:
                    del json_schema[k]  # redundant key
            if len(json_schema) > 1:
                # There is a remaining "override" key, so we need to move $ref out of the top level
                json_ref = JsonRef(json_schema['$ref'])
                del json_schema['$ref']
                assert 'allOf' not in json_schema  # this should never happen, but just in case
                json_schema['allOf'] = [{'$ref': json_ref}]

        return json_schema

    def get_schema_from_definitions(self, json_ref: JsonRef) -> JsonSchemaValue | None:
        return self.definitions.get(self.json_to_defs_refs[json_ref])

    def encode_default(self, dft: Any) -> Any:
        return pydantic_core.to_jsonable_python(dft)

    def update_with_validations(
        self, json_schema: JsonSchemaValue, core_schema: CoreSchema, mapping: dict[str, str]
    ) -> None:
        """
        Update the json_schema with the corresponding validations specified in the core_schema,
        using the provided mapping to translate keys in core_schema to the appropriate keys for a JSON schema.
        """
        for core_key, json_schema_key in mapping.items():
            if core_key in core_schema:
                json_schema[json_schema_key] = core_schema[core_key]  # type: ignore[literal-required]

    class ValidationsMapping:
        """
        This class just contains mappings from core_schema attribute names to the corresponding
        JSON schema attribute names. While I suspect it is unlikely to be necessary, you can in
        principle override this class in a subclass of GenerateJsonSchema (by inheriting from
        GenerateJsonSchema.ValidationsMapping) to change these mappings.
        """

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

    def get_flattened_anyof(self, schemas: list[JsonSchemaValue]) -> JsonSchemaValue:
        members = []
        for schema in schemas:
            if len(schema) == 1 and 'anyOf' in schema:
                members.extend(schema['anyOf'])
            else:
                members.append(schema)
        members = _deduplicate_schemas(members)
        if len(members) == 1:
            return members[0]
        return {'anyOf': members}

    def get_json_ref_counts(self, json_schema: JsonSchemaValue) -> dict[JsonRef, int]:
        """
        Get all values corresponding to the key '$ref' anywhere in the json_schema
        """
        json_refs: dict[JsonRef, int] = Counter()

        def _add_json_refs(schema: Any) -> None:
            if isinstance(schema, dict):
                if '$ref' in schema:
                    json_ref = JsonRef(schema['$ref'])
                    already_visited = json_ref in json_refs
                    json_refs[json_ref] += 1
                    if already_visited:
                        return  # prevent recursion on a definition that was already visited
                    _add_json_refs(self.definitions[self.json_to_defs_refs[json_ref]])
                for v in schema.values():
                    _add_json_refs(v)
            elif isinstance(schema, list):
                for v in schema:
                    _add_json_refs(v)

        _add_json_refs(json_schema)
        return json_refs

    def handle_invalid_for_json_schema(
        self, schema: CoreSchema | core_schema.TypedDictField | core_schema.DataclassField, error_info: str
    ) -> JsonSchemaValue:
        if _core_metadata.CoreMetadataHandler(schema).metadata.get('pydantic_js_modify_function') is not None:
            # Since there is a json schema modify function, assume that this type is meant to be handled,
            # and the modify function will set all properties as appropriate
            return {}
        else:
            raise PydanticInvalidForJsonSchema(f'Cannot generate a JsonSchema for {error_info}')

    def emit_warning(self, kind: JsonSchemaWarningKind, detail: str) -> None:
        """
        This method simply emits PydanticJsonSchemaWarnings based on handling in the `warning_message` method.
        """
        message = self.render_warning_message(kind, detail)
        if message is not None:
            warnings.warn(message, PydanticJsonSchemaWarning)

    def render_warning_message(self, kind: JsonSchemaWarningKind, detail: str) -> str | None:
        """
        This method is responsible for ignoring warnings as desired, and for formatting the warning messages.

        You can override the value of `ignored_warning_kinds` in a subclass of GenerateJsonSchema
        to modify what warnings are generated. If you want more control, you can override this method;
        just return None in situations where you don't want warnings to be emitted.
        """
        if kind in self.ignored_warning_kinds:
            return None
        return f'{detail} [{kind}]'


# ##### Start JSON Schema Generation Functions #####
# TODO: These should be moved to the pydantic.funcs module or whatever when appropriate.


def models_json_schema(
    models: Sequence[type[BaseModel] | type[PydanticDataclass]],
    *,
    by_alias: bool = True,
    title: str | None = None,
    description: str | None = None,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
) -> dict[str, Any]:
    # TODO: Put this in the "methods" module once that is created?
    instance = schema_generator(by_alias=by_alias, ref_template=ref_template)
    definitions = instance.generate_definitions([x.__pydantic_core_schema__ for x in models])

    json_schema: dict[str, Any] = {}
    if definitions:
        json_schema['$defs'] = definitions
    if title:
        json_schema['title'] = title
    if description:
        json_schema['description'] = description

    return json_schema


# TODO: Consider removing this cache, as it already gets used pretty infrequently.

if sys.version_info >= (3, 9):  # Typing for weak dictionaries available at 3.9
    _JsonSchemaCache = WeakKeyDictionary[Type[Any], Dict[Any, Any]]
else:
    _JsonSchemaCache = WeakKeyDictionary

_JSON_SCHEMA_CACHE = _JsonSchemaCache()


def model_json_schema(
    cls: type[BaseModel] | type[PydanticDataclass],
    by_alias: bool = True,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
) -> dict[str, Any]:
    # TODO: Put this in the "methods" module once that is created
    cls_json_schema_cache = _JSON_SCHEMA_CACHE.get(cls)
    if cls_json_schema_cache is None:
        _JSON_SCHEMA_CACHE[cls] = cls_json_schema_cache = {}

    cached = cls_json_schema_cache.get((by_alias, ref_template, schema_generator))
    if cached is not None:
        return cached

    json_schema = schema_generator(by_alias=by_alias, ref_template=ref_template).generate(cls.__pydantic_core_schema__)
    cls_json_schema_cache[(by_alias, ref_template, schema_generator)] = json_schema

    return json_schema


# ##### End JSON Schema Generation Functions #####


_Json = Union[Dict[str, Any], List[Any], str, int, float, bool, None]
_JsonDict = Dict[str, _Json]
_HashableJson = Union[Tuple[Tuple[str, Any], ...], Tuple[Any, ...], str, int, float, bool, None]


def _deduplicate_schemas(schemas: Iterable[_JsonDict]) -> list[_JsonDict]:
    return list({_make_json_hashable(schema): schema for schema in schemas}.values())


def _make_json_hashable(value: _Json) -> _HashableJson:
    if isinstance(value, dict):
        return tuple(sorted((k, _make_json_hashable(v)) for k, v in value.items()))
    elif isinstance(value, list):
        return tuple(_make_json_hashable(v) for v in value)
    else:
        return value
