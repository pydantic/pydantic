from __future__ import annotations

import re
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, is_dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional, cast

from pydantic_core import CoreSchema, core_schema
from typing_extensions import Literal

from pydantic._internal._typing_extra import all_literal_values, is_namedtuple
from pydantic.json import pydantic_encoder

JsonSchemaValue = Dict[str, Any]
JsonValue = Dict[str, Any]

JSON_SCHEMA_EXTRA_FIELD_NAME = 'pydantic_json_schema_extra'
default_ref_template = '#/definitions/{model}'


@dataclass
class JsonSchemaExtra:
    # see https://json-schema.org/understanding-json-schema/reference/generic.html

    title: Optional[str] = None  # from model config
    description: Optional[str] = None  # from model/enum docstring
    examples: Optional[list[JsonValue]] = None

    # 'default', which is included with these fields in the JsonSchema docs, is handled by CoreSchema
    deprecated: Optional[bool] = None
    read_only: Optional[bool] = None
    write_only: Optional[bool] = None

    comment: Optional[str] = None

    # Note: modify_schema is called after the schema has been updated based on the contents of all other fields
    modify_schema: Optional[Callable[[JsonSchemaValue], JsonSchemaValue]] = None

    def update_schema(self, schema: JsonSchemaValue) -> JsonSchemaValue:
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
        if self.modify_schema is not None:
            schema = self.modify_schema(schema)
        return schema


def get_json_schema_extra(schema: CoreSchema) -> Optional[JsonSchemaExtra]:
    extra = schema.get('extra', {})
    if not isinstance(extra, dict):
        return None
    json_schema_extra = extra.get(JSON_SCHEMA_EXTRA_FIELD_NAME)
    if json_schema_extra is not None:
        assert isinstance(json_schema_extra, JsonSchemaExtra)
    return json_schema_extra


# TODO: Can we put this definition in pydantic-core?
CoreSchemaType = Literal[
    'any',
    'none',
    'bool',
    'int',
    'float',
    'str',
    'bytes',
    'date',
    'time',
    'datetime',
    'timedelta',
    'literal',
    'is-instance',
    'is-subclass',
    'callable',
    'list',
    'tuple',
    'set',
    'frozenset',
    'generator',
    'dict',
    'function',
    'default',
    'nullable',
    'union',
    'tagged-union',
    'chain',
    'lax-or-strict',
    'typed-dict',
    'model',
    'arguments',
    'call',
    'recursive-ref',
    'custom-error',
    'json',
    'url',
    'multi-host-url',
]


class GenerateJsonSchema:
    def __init__(self, by_alias: bool = True, ref_template: str = default_ref_template, strict: bool = True):
        self.by_alias = by_alias
        self.ref_template = ref_template
        self.strict = strict  # if True, prefer the strict branch of LaxOrStrictSchema

        self.definitions: Dict[str, JsonSchemaValue] = {}

        self.core_to_json_refs: Dict[str, str] = {}
        self.json_to_core_refs: Dict[str, str] = {}

        self.json_ref_counts: Dict[str, int] = defaultdict(int)

    def generate(self, schema: CoreSchema) -> JsonSchemaValue:
        json_schema = self._generate(schema)

        # Remove top-level $ref if it isn't referenced elsewhere (i.e., not a recursive schema)
        if '$ref' in json_schema:
            json_schema_ref = json_schema['$ref']
            if self.json_ref_counts[json_schema_ref] == 1:
                ref_key = json_schema_ref.split('/')[-1]
                if ref_key in self.definitions:
                    del json_schema['$ref']
                    json_schema.update(deepcopy(self.definitions[ref_key]))
                    self.definitions.pop(ref_key)

        if self.definitions:
            json_schema['definitions'] = self.definitions
        return json_schema

    def _generate(self, schema: CoreSchema) -> JsonSchemaValue:
        # TODO: Note: the approach to caching here only caches intermediate computations for *this* CoreSchema.
        #   In particular, the schema for intermediate models will not be cached; this may be undesirable.
        #   I'm not sure what the best way to handle this is; perhaps a global cache accounting
        #   for the settings of the GenerateJsonSchema instance, perhaps not

        # Try to load from the "cache"
        if 'ref' in schema:
            core_ref: str = schema['ref']  # type: ignore[typeddict-item]
            if core_ref in self.core_to_json_refs:
                return self.definitions[self.core_to_json_refs[core_ref]]

        # Handle the type-specific bits of the schema generation
        generate_for_schema_type = _JSON_SCHEMA_METHOD_MAPPING[schema['type']]
        json_schema = generate_for_schema_type(self, schema)

        # Handle the "generic" bits of the schema generation
        extra = get_json_schema_extra(schema)
        if extra is not None:
            extra.update_schema(json_schema)

        # Populate the "cache"
        if 'ref' in schema:
            core_ref = schema['ref']  # type: ignore[typeddict-item]
            json_ref = self.get_json_ref(core_ref)
            self.definitions[json_ref] = json_schema
            return self._ref_json_schema(json_ref)

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

        json_ref = re.sub(r'[^a-zA-Z0-9.\-_]', '_', core_ref)
        while self.json_to_core_refs.get(json_ref, core_ref) != core_ref:
            # Hitting a collision; add trailing `_` until we don't hit a collision
            # TODO: Maybe add an incrementing counter to the end of the json_ref instead?
            json_ref += '_'

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
        json_schema = {'type': 'string'}
        update_with_validations(json_schema, schema, ValidationsMapping.bytes)
        return json_schema

    def date_schema(self, schema: core_schema.DateSchema) -> JsonSchemaValue:
        # TODO: do we want to handle the "pattern" field?
        return {'type': 'string', 'format': 'date'}

    def time_schema(self, schema: core_schema.TimeSchema) -> JsonSchemaValue:
        return {'type': 'string', 'format': 'time'}

    def datetime_schema(self, schema: core_schema.DatetimeSchema) -> JsonSchemaValue:
        return {'type': 'string', 'format': 'date-time'}

    def timedelta_schema(self, schema: core_schema.TimedeltaSchema) -> JsonSchemaValue:
        return {'type': 'string', 'format': 'time-delta'}

    def literal_schema(self, schema: core_schema.LiteralSchema) -> JsonSchemaValue:
        expected = schema['expected']
        if len(expected) == 1:
            return {'const': expected[0]}
        else:
            return {'enum': expected}

    def is_instance_schema(self, schema: core_schema.IsInstanceSchema) -> JsonSchemaValue:
        # TODO: Ask Samuel how to handle this
        # raise ValueError('Cannot generate a JsonSchema for core_schema.IsInstanceSchema')
        return {}

    def is_subclass_schema(self, schema: core_schema.IsSubclassSchema) -> JsonSchemaValue:
        # TODO: Ask Samuel how to handle this
        # raise ValueError('Cannot generate a JsonSchema for core_schema.IsSubclassSchema')
        return {}

    def callable_schema(self, schema: core_schema.CallableSchema) -> JsonSchemaValue:
        # TODO: Ask Samuel how to handle this
        # raise ValueError('Cannot generate a JsonSchema for core_schema.CallableSchema')
        return {}

    def list_schema(self, schema: core_schema.ListSchema) -> JsonSchemaValue:
        json_schema = {'type': 'array'}
        update_with_validations(json_schema, schema, ValidationsMapping.array)
        return json_schema

    def tuple_schema(
        self, schema: core_schema.TupleVariableSchema | core_schema.TuplePositionalSchema
    ) -> JsonSchemaValue:
        json_schema = {'type': 'array'}
        if schema['mode'] == 'tuple-variable':
            json_schema['items'] = self._generate(schema['items_schema'])
            update_with_validations(json_schema, schema, ValidationsMapping.array)
            return json_schema

        elif schema['mode'] == 'tuple-positional':
            json_schema['prefixItems'] = [self._generate(item) for item in schema['items_schema']]
            json_schema['minLength'] = len(schema['items_schema'])
            if 'extra_schema' in schema:
                # TODO: What is schema['extra_schema'] meant to handle? I'm not sure this could arise from typing.Tuple
                json_schema['items'] = self._generate(schema['extra_schema'])
            else:
                json_schema['maxLength'] = len(schema['items_schema'])
            return json_schema

        else:
            raise ValueError(f'Unknown tuple schema mode: {schema["mode"]}')

    def set_schema(self, schema: core_schema.SetSchema) -> JsonSchemaValue:
        return self._common_set_schema(schema)

    def frozenset_schema(self, schema: core_schema.FrozenSetSchema) -> JsonSchemaValue:
        return self._common_set_schema(schema)

    def _common_set_schema(self, schema: core_schema.SetSchema | core_schema.FrozenSetSchema) -> JsonSchemaValue:
        # TODO: what is schema['generator_max_length']?
        items_schema = self._generate(schema['items_schema'])
        json_schema = {'type': 'array', 'uniqueItems': True, 'items': items_schema}
        update_with_validations(json_schema, schema, ValidationsMapping.array)
        return json_schema

    def generator_schema(self, schema: core_schema.GeneratorSchema) -> JsonSchemaValue:
        # TODO: Why no min_length? Is max_length validated on ingestion?
        items_schema = self._generate(schema['items_schema'])
        json_schema = {'type': 'array', 'items': items_schema}
        update_with_validations(json_schema, schema, ValidationsMapping.array)
        return json_schema

    def dict_schema(self, schema: core_schema.DictSchema) -> JsonSchemaValue:
        values_schema = self._generate(schema['values_schema'])
        json_schema = {'type': 'object', 'additionalProperties': values_schema}
        update_with_validations(json_schema, schema, ValidationsMapping.object)
        return json_schema

    def function_schema(self, schema: core_schema.FunctionSchema) -> JsonSchemaValue:
        # TODO: Ask Samuel if this is right; I'm not sure if before vs. after affects things
        return self._generate(schema['schema'])

    def default_schema(self, schema: core_schema.WithDefaultSchema) -> JsonSchemaValue:
        json_schema = self._generate(schema['schema'])
        if 'default' in schema:
            json_schema['default'] = encode_default(schema['default'])
        return json_schema

    def nullable_schema(self, schema: core_schema.NullableSchema) -> JsonSchemaValue:
        null_schema = {'type': 'null'}
        inner_json_schema = self._generate(schema['schema'])

        if inner_json_schema == null_schema:
            return null_schema
        else:
            # TODO: Should this be oneOf instead? I think both would be valid here; not sure if one is better..
            return {'anyOf': [null_schema, inner_json_schema]}

    def union_schema(self, schema: core_schema.UnionSchema) -> JsonSchemaValue:
        return {'anyOf': [self._generate(s) for s in schema['choices']]}

    def tagged_union_schema(self, schema: core_schema.TaggedUnionSchema) -> JsonSchemaValue:
        # TODO: May want to add discriminator here; depends on dialect etc.
        # TODO: Do we need to do anything with custom_error_xxx?
        # TODO: Ask samuel what is going on with the different non-`str` variants of `schema.discriminator`
        return {'oneOf': [self._generate(s) for s in schema['choices'].values() if not isinstance(s, str)]}

    def chain_schema(self, schema: core_schema.ChainSchema) -> JsonSchemaValue:
        if not schema['steps']:
            # TODO: Ask Samuel -- what do we do if there are no items in the ChainSchema?
            raise ValueError('Cannot generate a JsonSchema for a zero-step ChainSchema')
        return self._generate(schema['steps'][-1])

    def lax_or_strict_schema(self, schema: core_schema.LaxOrStrictSchema) -> JsonSchemaValue:
        # TODO: Ask Samuel what `schema.strict` is meant to represent here
        if self.strict:
            return self._generate(schema['strict_schema'])
        else:
            return self._generate(schema['lax_schema'])

    def typed_dict_schema(self, schema: core_schema.TypedDictSchema) -> JsonSchemaValue:
        properties: Dict[str, JsonSchemaValue] = {}
        required: list[str] = []
        for name, field in schema['fields'].items():
            if field['required']:
                required.append(name)
            if self.by_alias:
                alias = field.get('validation_alias', name)
                if isinstance(alias, str):
                    name = alias
                else:
                    # TODO: What should be done in this case?
                    pass
            field_schema = self._generate(field['schema'])
            field_schema.setdefault('title', name.title().replace('_', ' '))
            properties[name] = field_schema

        json_schema = {'type': 'object', 'properties': properties}
        if required:
            json_schema['required'] = required
        return json_schema

    def model_schema(self, schema: core_schema.ModelSchema) -> JsonSchemaValue:
        # TODO: Note the relationship between this and TypedDictSchema
        #   -- Should we do something similar with LiteralSchema and a possibly-new EnumSchema?
        json_schema = self._generate(schema['schema'])

        # TODO: Store generated schema in the schema['cls'].__schema_cache__ or similar?

        # TODO: What should we do with schema['config'] (in particular, 'title')?
        #   Also, what is schema['call_after_init']?
        if 'config' in schema and 'title' in schema['config']:
            json_schema.setdefault('title', schema['config']['title'])
        return json_schema

    def arguments_schema(self, schema: core_schema.ArgumentsSchema) -> JsonSchemaValue:
        # TODO: Ask Samuel how to handle this
        # raise ValueError('Cannot generate a JsonSchema for core_schema.ArgumentsSchema')
        return {}

    def call_schema(self, schema: core_schema.CallSchema) -> JsonSchemaValue:
        # TODO: Ask Samuel how to handle this
        # raise ValueError('Cannot generate a JsonSchema for core_schema.CallSchema')
        return {}

    def recursive_ref_schema(self, schema: core_schema.RecursiveReferenceSchema) -> JsonSchemaValue:
        json_ref = self.get_json_ref(schema['schema_ref'])
        return self._ref_json_schema(json_ref)

    def _ref_json_schema(self, json_ref: str) -> JsonSchemaValue:
        json_ref = self.ref_template.format(model=json_ref)
        self.json_ref_counts[json_ref] += 1
        return {'$ref': json_ref}

    def custom_error_schema(self, schema: core_schema.CustomErrorSchema) -> JsonSchemaValue:
        # TODO: Ask Samuel how to handle this
        # raise ValueError('Cannot generate a JsonSchema for core_schema.CustomErrorSchema')
        return {}

    def json_schema(self, schema: core_schema.JsonSchema) -> JsonSchemaValue:
        return {'type': 'string', 'format': 'json-string'}

    def url_schema(self, schema: core_schema.UrlSchema) -> JsonSchemaValue:
        json_schema = {'type': 'string', 'format': 'uri', 'minLength': 1}
        update_with_validations(json_schema, schema, ValidationsMapping.string)
        return json_schema

    def multi_host_url_schema(self, schema: core_schema.MultiHostUrlSchema) -> JsonSchemaValue:
        # TODO: Is 'format': 'uri' valid for MultiHostUrlSchema? I'm not sure
        json_schema = {'type': 'string', 'format': 'uri', 'minLength': 1}
        update_with_validations(json_schema, schema, ValidationsMapping.string)
        return json_schema


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
        'regex': 'pattern',
    }
    array = {
        'min_length': 'minItems',
        'max_length': 'maxItems',
    }
    object = {
        'min_length': 'minProperties',
        'max_length': 'maxProperties',
    }


def update_with_validations(json_schema: JsonSchemaValue, core_schema: CoreSchema, mapping: Dict[str, str]) -> None:
    for core_key, json_schema_key in mapping.items():
        if core_key in core_schema:
            json_schema[json_schema_key] = core_schema[core_key]  # type: ignore[literal-required]


# Technically the second argument to the callables below will be a specific subtype of CoreSchema.
# We just need to make sure elsewhere that each callable only gets called on CoreSchema objects of
# properly matched type.
def _build_json_schema_method_mapping() -> Dict[str, Callable[[GenerateJsonSchema, CoreSchema], JsonSchemaValue]]:
    mapping: Dict[str, Callable[[GenerateJsonSchema, CoreSchema], JsonSchemaValue]] = {}
    for key in all_literal_values(CoreSchemaType):  # type: ignore[arg-type]
        method_key = key.replace('-', '_')
        mapping[key] = getattr(GenerateJsonSchema, f'{method_key}_schema')
    return mapping


_JSON_SCHEMA_METHOD_MAPPING = _build_json_schema_method_mapping()


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
