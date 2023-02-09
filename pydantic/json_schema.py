"""
Super annoying thing: changing the default value of a field means it can't use the same schema as a $ref...
In particular, a default value of None for a required field means it can't be a $ref.

I guess this means I have to figure out how to implement optional in a better way...?
"""
from __future__ import annotations

import re
from dataclasses import dataclass, is_dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional, Set, cast

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


def _get_json_refs(json_schema: JsonSchemaValue) -> Set[str]:
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


# TODO: Probably want a public API for using a subclass of this so users can override their schema generation
class GenerateJsonSchema:
    def __init__(self, by_alias: bool = True, ref_template: str = default_ref_template, strict: bool = True):
        self.by_alias = by_alias
        self.ref_template = ref_template
        self.strict = strict  # if True, prefer the strict branch of LaxOrStrictSchema

        self.definitions: Dict[str, JsonSchemaValue] = {}

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
        self.core_to_json_refs: Dict[str, str] = {}
        self.json_to_core_refs: Dict[str, str] = {}
        self.json_to_defs_refs: Dict[str, str] = {}

    def generate(self, schema: CoreSchema) -> JsonSchemaValue:
        json_schema = self._generate(schema)

        # Remove the top-level $ref if present; note that the _generate method already ensures there are no sibling keys
        if '$ref' in json_schema:
            json_schema_ref = json_schema['$ref']
            json_schema = self._get_referenced_schema(json_schema_ref)

        # Remove any definitions that, thanks to $ref-substitution, are no longer present
        # TODO: Add a unit test for this, ensuring that $ref substitution does in fact cause the removal of definitions
        remaining_json_refs = _get_json_refs(json_schema)
        all_json_refs = list(self.json_to_defs_refs.keys())
        for k in all_json_refs:
            if k not in remaining_json_refs:
                del self.definitions[self.json_to_defs_refs[k]]

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
        json_schema: Dict[str, str] = generate_for_schema_type(self, schema)

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

        # Remove top-level $ref if there are sibling keys -- this is necessary since $ref replaces all other keys
        # (see bottom of https://swagger.io/docs/specification/using-ref/ for reference)
        if '$ref' in json_schema:
            json_schema_ref = json_schema['$ref']
            referenced_json_schema = self._get_referenced_schema(json_schema_ref)
            overrides = False
            for k in json_schema:
                if k == '$ref':
                    continue
                if k not in referenced_json_schema or json_schema[k] != referenced_json_schema[k]:
                    overrides = True
                    break
            if not overrides:
                # All sibling keys were redundant, and therefore safe to remove
                return {'$ref': json_schema_ref}
            else:
                json_schema = json_schema.copy()
                json_schema_ref = json_schema.pop('$ref')
                for k, v in referenced_json_schema.items():
                    # Use setdefault to treat the sibling keys of the '$ref' as "overrides"
                    json_schema.setdefault(k, v)

        if '$ref' in json_schema:
            assert len(json_schema) == 1
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
            # TODO: Maybe add an incrementing counter to the end of the json_ref instead?
            #   Probably safest to use the same approach as v1 (from perspective of people complaining)
            # TODO: Note, if we load cached schemas from other models, may need to ensure refs are consistent
            json_ref += '_'
            # possible improvement: AModel, AModel:2, AModel:3, AModel:4
            # Other possibility: allow people to subclass this class for purposes of overriding
            #   maybe start with all this stuff being private and expose it if people ask for it

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
        return {'type': 'string', 'format': 'date'}

    def time_schema(self, schema: core_schema.TimeSchema) -> JsonSchemaValue:
        return {'type': 'string', 'format': 'time'}

    def datetime_schema(self, schema: core_schema.DatetimeSchema) -> JsonSchemaValue:
        return {'type': 'string', 'format': 'date-time'}

    def timedelta_schema(self, schema: core_schema.TimedeltaSchema) -> JsonSchemaValue:
        # TODO: Add comment about why there is a format specified for 'type': 'number'
        #  (Also consider changing to type string)
        # TODO: Probably should just change this to str
        #   (look at readme intro for speeddate)
        return {'type': 'number', 'format': 'time-delta'}

    def literal_schema(self, schema: core_schema.LiteralSchema) -> JsonSchemaValue:
        expected = schema['expected']
        if len(expected) == 1:
            return {'const': expected[0]}
        else:
            return {'enum': expected}

    def is_instance_schema(self, schema: core_schema.IsInstanceSchema) -> JsonSchemaValue:
        # TODO: Ask Samuel how to handle this
        # TODO: Should we exclude cases like this from unions? Raise an error, catch it in unions
        #   Otherwise, add any with a comment? Or return none?
        # raise ValueError('Cannot generate a JsonSchema for core_schema.IsInstanceSchema')
        return {}  # TODO: add a $comment indicating info about the core schema?

    def is_subclass_schema(self, schema: core_schema.IsSubclassSchema) -> JsonSchemaValue:
        # TODO: Ask Samuel how to handle this
        # raise ValueError('Cannot generate a JsonSchema for core_schema.IsSubclassSchema')
        return {}

    def callable_schema(self, schema: core_schema.CallableSchema) -> JsonSchemaValue:
        # TODO: Ask Samuel how to handle this
        # raise ValueError('Cannot generate a JsonSchema for core_schema.CallableSchema')
        return {}

    def list_schema(self, schema: core_schema.ListSchema) -> JsonSchemaValue:
        items_schema = self._generate(schema['items_schema'])
        json_schema = {'type': 'array', 'items': items_schema}
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
                # TODO: Add a comment into core_schema about this, since typing.Tuple can't
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
        # TODO: Add description of generator_max_length into core_schema --
        #   idea: don't want to run a generator forever if it's not spitting out unique values
        items_schema = self._generate(schema['items_schema'])
        json_schema = {'type': 'array', 'uniqueItems': True, 'items': items_schema}
        update_with_validations(json_schema, schema, ValidationsMapping.array)
        return json_schema

    def generator_schema(self, schema: core_schema.GeneratorSchema) -> JsonSchemaValue:
        # TODO: Why no min_length? Is max_length validated on ingestion?
        #   -- yes, max_length is validated on ingestion; might make sense to add a min_length?
        items_schema = self._generate(schema['items_schema'])
        json_schema = {'type': 'array', 'items': items_schema}
        update_with_validations(json_schema, schema, ValidationsMapping.array)
        return json_schema

    def dict_schema(self, schema: core_schema.DictSchema) -> JsonSchemaValue:
        values_schema = self._generate(schema['values_schema']).copy()
        values_schema.pop('title', None)  # don't give a title to the additionalProperties

        json_schema: JsonSchemaValue = {'type': 'object'}
        if values_schema:  # don't add additionalProperties if it's empty
            json_schema['additionalProperties'] = values_schema

        update_with_validations(json_schema, schema, ValidationsMapping.object)
        return json_schema

    def function_schema(self, schema: core_schema.FunctionSchema) -> JsonSchemaValue:
        # TODO: Ask Samuel if this is right; I'm not sure if before vs. after affects things
        return self._generate(schema['schema'])

    def default_schema(self, schema: core_schema.WithDefaultSchema) -> JsonSchemaValue:
        json_schema = self._generate(schema['schema'])
        if 'default' in schema:
            json_schema['default'] = encode_default(schema['default'])
        elif 'default_factory' in schema:
            json_schema['default'] = encode_default(schema['default_factory']())
        else:
            raise ValueError('`schema` has neither default nor default_factory')
        return json_schema

    def nullable_schema(self, schema: core_schema.NullableSchema) -> JsonSchemaValue:
        null_schema = {'type': 'null'}
        inner_json_schema = self._generate(schema['schema'])

        if inner_json_schema == null_schema:
            return null_schema
        else:
            # TODO: Should this be oneOf instead? I think both would be valid here; not sure if one is better..
            # TODO: Search for this in issues in v1, to see if we should change it to oneOf
            return {'anyOf': [null_schema, inner_json_schema]}

    def union_schema(self, schema: core_schema.UnionSchema) -> JsonSchemaValue:
        # TODO: Handle case where one of the union members should not be added to the JsonSchema (?)
        #  if an error is raised or whatever
        # TODO: Always unpack if there's just one item in the UnionSchema
        # TODO: Figure out what to do if anyOf list is empty
        return {'anyOf': [self._generate(s) for s in schema['choices']]}

    def tagged_union_schema(self, schema: core_schema.TaggedUnionSchema) -> JsonSchemaValue:
        # TODO: May want to add discriminator here; depends on dialect etc.
        # TODO: Do we need to do anything with custom_error_xxx?
        # TODO: Ask samuel what is going on with the different non-`str` variants of `schema.discriminator`
        # TODO: Add note in pydantic_core explaining the choices; for list,
        #  it goes deep; for list of lists, it has multiple options
        #  Probably want to just ignore discriminator things when the discriminator is not a list
        return {'oneOf': [self._generate(s) for s in schema['choices'].values() if not isinstance(s, str)]}

    def chain_schema(self, schema: core_schema.ChainSchema) -> JsonSchemaValue:
        try:
            # Note: If we wanted to generate a schema for the _serialization_, would want to use the _last_ step:
            return self._generate(schema['steps'][0])
        except IndexError as e:
            raise ValueError('Cannot generate a JsonSchema for a zero-step ChainSchema') from e

    def lax_or_strict_schema(self, schema: core_schema.LaxOrStrictSchema) -> JsonSchemaValue:
        # TODO: How should `schema.strict` factor into this? Should it at all?
        #   -- might be possible to drop it from core_schema.LaxOrStrictSchema
        if self.strict:
            return self._generate(schema['strict_schema'])
        else:
            return self._generate(schema['lax_schema'])

    def typed_dict_schema(self, schema: core_schema.TypedDictSchema) -> JsonSchemaValue:
        # TODO: Hitting an issue where it would be really helpful to have the 'title' when I have the ref.
        # TODO: Create an issue to consider moving ref from the TypedDictSchema to the ModelSchema
        #   In particular, explain why this is problematic during schema generation

        # Specifically, making it hard to get title set properly on the referenced schemas
        # Ideally, the ref would be on the ModelSchema, not on the TypedDictSchema
        properties: Dict[str, JsonSchemaValue] = {}
        required: list[str] = []
        for name, field in schema['fields'].items():
            if self.by_alias:
                alias = field.get('validation_alias', name)
                if isinstance(alias, str):
                    name = alias
                else:
                    # TODO: What should be done in this case?
                    #   Maybe tell users to override this method if they want custom behavior here?
                    #       (If populate by name is false)
                    pass
            field_schema = self._generate(field['schema']).copy()
            field_schema['title'] = name.title().replace('_', ' ')
            properties[name] = field_schema
            if field['required']:
                required.append(name)

        json_schema = {'type': 'object', 'properties': properties}
        if required:
            json_schema['required'] = required
        return json_schema

    def _get_referenced_schema(self, json_ref: str) -> JsonSchemaValue:
        return self.definitions[self.json_to_defs_refs[json_ref]]

    def model_schema(self, schema: core_schema.ModelSchema) -> JsonSchemaValue:
        # TODO: -- Try to pull the schema off the schema.cls, and use the method to grab the value
        #   Maybe: need to add cache keys related to parent class; maybe want to

        # TODO: Note the relationship between this and TypedDictSchema
        #   -- Should we do something similar with LiteralSchema and a possibly-new EnumSchema?
        #   Main reason not to: Enums aren't special in C API, so maybe not appropriate in pydantic_core
        #       However, we can introspect the FunctionSchema to see if it's an enum (or use extra),
        #       and we _should_ put enums into the definitions
        json_schema = self._generate(schema['schema'])

        # TODO: What should we do with schema['config'] (in particular, 'title')?
        #   Also, what is schema['call_after_init']?
        if 'config' in schema and 'title' in schema['config']:
            title = schema['config']['title']
            if '$ref' in json_schema:
                # hack: update the definition from the typed_dict_schema to include the title
                self._get_referenced_schema(json_schema['$ref'])['title'] = title
            else:
                json_schema.setdefault('title', title)
        return json_schema

    def arguments_schema(self, schema: core_schema.ArgumentsSchema) -> JsonSchemaValue:
        # TODO: Need to figure out how to handle this
        # raise ValueError('Cannot generate a JsonSchema for core_schema.ArgumentsSchema')
        raise NotImplementedError
        # return {}

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
    # Convert this to a unit test that checks the methods are defined
    mapping: Dict[str, Callable[[GenerateJsonSchema, CoreSchema], JsonSchemaValue]] = {}
    for key in all_literal_values(CoreSchemaType):  # type: ignore[arg-type]
        method_name = f"{key.replace('-', '_')}_schema"
        try:
            mapping[key] = getattr(GenerateJsonSchema, method_name)
        except AttributeError:
            raise TypeError(
                f'No method for generating JsonSchema for core_schema.type={key!r} '
                f'(expected: GenerateJsonSchema.{method_name})'
            )
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
