from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Sequence, Set, Tuple, Type
from uuid import UUID

from . import main
from .fields import Field, Shape
from .json import pydantic_encoder
from .types import DSN, UUID1, UUID3, UUID4, UUID5, DirectoryPath, EmailStr, FilePath, Json, NameEmail, UrlStr
from .utils import clean_docstring

__all__ = [
    'schema',
    'model_schema',
    'field_schema',
    'get_model_name_map',
    'get_flat_models_from_model',
    'get_flat_models_from_field',
    'get_flat_models_from_fields',
    'get_flat_models_from_models',
    'get_long_model_name',
    'field_type_schema',
    'model_process_schema',
    'model_type_schema',
    'field_singleton_sub_fields_schema',
    'field_singleton_schema',
]

default_prefix = '#/definitions/'


def schema(
    models: Sequence[Type['main.BaseModel']], *, by_alias=True, title=None, description=None, ref_prefix=None
) -> Dict:
    """
    Process a list of models and generate a single JSON Schema with all of them defined in the ``definitions``
    top-level JSON key, including their sub-models.

    :param models: a list of models to include in the generated JSON Schema
    :param by_alias: generate the schemas using the aliases defined, if any
    :param title: title for the generated schema that includes the definitions
    :param description: description for the generated schema
    :param ref_prefix: the JSON Pointer prefix for schema references with ``$ref``, if None, will be set to the
      default of ``#/definitions/``. Update it if you want the schemas to reference the definitions somewhere
      else, e.g. for OpenAPI use ``#/components/schemas/``. The resulting generated schemas will still be at the
      top-level key ``definitions``, so you can extract them from there. But all the references will have the set
      prefix.
    :return: dict with the JSON Schema with a ``definitions`` top-level key including the schema definitions for
      the models and sub-models passed in ``models``.
    """
    ref_prefix = ref_prefix or default_prefix
    flat_models = get_flat_models_from_models(models)
    model_name_map = get_model_name_map(flat_models)
    definitions = {}
    output_schema = {}
    if title:
        output_schema['title'] = title
    if description:
        output_schema['description'] = description
    for model in models:
        m_schema, m_definitions = model_process_schema(
            model, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
        )
        definitions.update(m_definitions)
        model_name = model_name_map[model]
        definitions[model_name] = m_schema
    if definitions:
        output_schema['definitions'] = definitions
    return output_schema


def model_schema(model: Type['main.BaseModel'], by_alias=True, ref_prefix=None) -> Dict[str, Any]:
    """
    Generate a JSON Schema for one model. With all the sub-models defined in the ``definitions`` top-level
    JSON key.

    :param model: a Pydantic model (a class that inherits from BaseModel)
    :param by_alias: generate the schemas using the aliases defined, if any
    :param ref_prefix: the JSON Pointer prefix for schema references with ``$ref``, if None, will be set to the
      default of ``#/definitions/``. Update it if you want the schemas to reference the definitions somewhere
      else, e.g. for OpenAPI use ``#/components/schemas/``. The resulting generated schemas will still be at the
      top-level key ``definitions``, so you can extract them from there. But all the references will have the set
      prefix.
    :return: dict with the JSON Schema for the passed ``model``
    """
    ref_prefix = ref_prefix or default_prefix
    flat_models = get_flat_models_from_model(model)
    model_name_map = get_model_name_map(flat_models)
    m_schema, m_definitions = model_process_schema(
        model, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
    )
    if m_definitions:
        m_schema.update({'definitions': m_definitions})
    return m_schema


def field_schema(
    field: Field, *, by_alias=True, model_name_map: Dict[Type['main.BaseModel'], str], ref_prefix=None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Process a Pydantic field and return a tuple with a JSON Schema for it as the first item.
    Also return a dictionary of definitions with models as keys and their schemas as values. If the passed field
    is a model and has sub-models, and those sub-models don't have overrides (as ``title``, ``default``, etc), they
    will be included in the definitions and referenced in the schema instead of included recursively.

    :param field: a Pydantic ``Field``
    :param by_alias: use the defined alias (if any) in the returned schema
    :param model_name_map: used to generate the JSON Schema references to other models included in the definitions
    :param ref_prefix: the JSON Pointer prefix to use for references to other schemas, if None, the default of
      #/definitions/ will be used
    :return: tuple of the schema for this field and additional definitions
    """
    ref_prefix = ref_prefix or default_prefix
    schema_overrides = False
    s = dict(title=field._schema.title or field.alias.title())
    if field._schema.title:
        schema_overrides = True

    if field._schema.description:
        s['description'] = field._schema.description
        schema_overrides = True

    if not field.required and field.default is not None:
        s['default'] = encode_default(field.default)
        schema_overrides = True

    validation_schema = get_field_schema_validations(field)
    if validation_schema:
        s.update(validation_schema)
        schema_overrides = True

    f_schema, f_definitions = field_type_schema(
        field,
        by_alias=by_alias,
        model_name_map=model_name_map,
        schema_overrides=schema_overrides,
        ref_prefix=ref_prefix,
    )
    # $ref will only be returned when there are no schema_overrides
    if '$ref' in f_schema:
        return f_schema, f_definitions
    else:
        s.update(f_schema)
        return s, f_definitions


numeric_types = (int, float, Decimal)
_str_types_attrs = {
    'max_length': (numeric_types, 'maxLength'),
    'min_length': (numeric_types, 'minLength'),
    'regex': (str, 'pattern'),
}
_numeric_types_attrs = {
    'gt': (numeric_types, 'exclusiveMinimum'),
    'lt': (numeric_types, 'exclusiveMaximum'),
    'ge': (numeric_types, 'minimum'),
    'le': (numeric_types, 'maximum'),
}


def get_field_schema_validations(field):
    """Get the JSON Schema validation keywords for a ``field`` with an annotation of
      a Pydantic ``Schema`` with validation arguments.
    """
    f_schema = {}
    if isinstance(field.type_, type) and issubclass(field.type_, (str, bytes)):
        for attr, (t, keyword) in _str_types_attrs.items():
            if getattr(field._schema, attr) and isinstance(getattr(field._schema, attr), t):
                f_schema[keyword] = getattr(field._schema, attr)
    if isinstance(field.type_, type) and issubclass(field.type_, numeric_types) and not issubclass(field.type_, bool):
        for attr, (t, keyword) in _numeric_types_attrs.items():
            if getattr(field._schema, attr) and isinstance(getattr(field._schema, attr), t):
                f_schema[keyword] = getattr(field._schema, attr)
    if field._schema.extra:
        f_schema.update(field._schema.extra)
    return f_schema


def get_model_name_map(unique_models: Set[Type['main.BaseModel']]) -> Dict[Type['main.BaseModel'], str]:
    """
    Process a set of models and generate unique names for them to be used as keys in the JSON Schema
    definitions. By default the names are the same as the class name. But if two models in different Python
    modules have the same name (e.g. "users.Model" and "items.Model"), the generated names will be
    based on the Python module path for those conflicting models to prevent name collisions.

    :param unique_models: a Python set of models
    :return: dict mapping models to names
    """
    name_model_map = {}
    conflicting_names = set()
    for model in unique_models:
        model_name = model.__name__
        if model_name in conflicting_names:
            model_name = get_long_model_name(model)
            name_model_map[model_name] = model
        elif model_name in name_model_map:
            conflicting_names.add(model_name)
            conflicting_model = name_model_map.pop(model_name)
            name_model_map[get_long_model_name(conflicting_model)] = conflicting_model
            name_model_map[get_long_model_name(model)] = model
        else:
            name_model_map[model_name] = model
    return {v: k for k, v in name_model_map.items()}


def get_flat_models_from_model(model: Type['main.BaseModel']) -> Set[Type['main.BaseModel']]:
    """
    Take a single ``model`` and generate a set with itself and all the sub-models in the tree. I.e. if you pass
    model ``Foo`` (subclass of Pydantic ``BaseModel``) as ``model``, and it has a field of type ``Bar`` (also
    subclass of ``BaseModel``) and that model ``Bar`` has a field of type ``Baz`` (also subclass of ``BaseModel``),
    the return value will be ``set([Foo, Bar, Baz])``.

    :param model: a Pydantic ``BaseModel`` subclass
    :return: a set with the initial model and all its sub-models
    """
    flat_models = set()
    flat_models.add(model)
    flat_models |= get_flat_models_from_fields(model.__fields__.values())
    return flat_models


def get_flat_models_from_field(field: Field) -> Set[Type['main.BaseModel']]:
    """
    Take a single Pydantic ``Field`` (from a model) that could have been declared as a sublcass of BaseModel
    (so, it could be a submodel), and generate a set with its model and all the sub-models in the tree.
    I.e. if you pass a field that was declared to be of type ``Foo`` (subclass of BaseModel) as ``field``, and that
    model ``Foo`` has a field of type ``Bar`` (also subclass of ``BaseModel``) and that model ``Bar`` has a field of
    type ``Baz`` (also subclass of ``BaseModel``), the return value will be ``set([Foo, Bar, Baz])``.

    :param field: a Pydantic ``Field``
    :return: a set with the model used in the declaration for this field, if any, and all its sub-models
    """
    flat_models = set()
    if field.sub_fields:
        flat_models |= get_flat_models_from_fields(field.sub_fields)
    elif isinstance(field.type_, type) and issubclass(field.type_, main.BaseModel):
        flat_models |= get_flat_models_from_model(field.type_)
    return flat_models


def get_flat_models_from_fields(fields) -> Set[Type['main.BaseModel']]:
    """
    Take a list of Pydantic  ``Field``s (from a model) that could have been declared as sublcasses of ``BaseModel``
    (so, any of them could be a submodel), and generate a set with their models and all the sub-models in the tree.
    I.e. if you pass a the fields of a model ``Foo`` (subclass of ``BaseModel``) as ``fields``, and on of them has a
    field of type ``Bar`` (also subclass of ``BaseModel``) and that model ``Bar`` has a field of type ``Baz`` (also
    subclass of ``BaseModel``), the return value will be ``set([Foo, Bar, Baz])``.

    :param fields: a list of Pydantic ``Field``s
    :return: a set with any model declared in the fields, and all their sub-models
    """
    flat_models = set()
    for field in fields:
        flat_models |= get_flat_models_from_field(field)
    return flat_models


def get_flat_models_from_models(models: Sequence[Type['main.BaseModel']]) -> Set[Type['main.BaseModel']]:
    """
    Take a list of ``models`` and generate a set with them and all their sub-models in their trees. I.e. if you pass
    a list of two models, ``Foo`` and ``Bar``, both subclasses of Pydantic ``BaseModel`` as models, and ``Bar`` has
    a field of type ``Baz`` (also subclass of ``BaseModel``), the return value will be ``set([Foo, Bar, Baz])``.
    """
    flat_models = set()
    for model in models:
        flat_models |= get_flat_models_from_model(model)
    return flat_models


def get_long_model_name(model: Type['main.BaseModel']):
    return f'{model.__module__}__{model.__name__}'.replace('.', '__')


def field_type_schema(
    field: Field,
    *,
    by_alias: bool,
    model_name_map: Dict[Type['main.BaseModel'], str],
    schema_overrides=False,
    ref_prefix=None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Used by ``field_schema()``, you probably should be using that function.

    Take a single ``field`` and generate the schema for its type only, not including additional
    information as title, etc. Also return additional schema definitions, from sub-models.
    """
    definitions = {}
    ref_prefix = ref_prefix or default_prefix
    if field.shape is Shape.LIST:
        f_schema, f_definitions = field_singleton_schema(
            field, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
        )
        definitions.update(f_definitions)
        return {'type': 'array', 'items': f_schema}, definitions
    elif field.shape is Shape.SET:
        f_schema, f_definitions = field_singleton_schema(
            field, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
        )
        definitions.update(f_definitions)
        return {'type': 'array', 'uniqueItems': True, 'items': f_schema}, definitions
    elif field.shape is Shape.MAPPING:
        f_schema, f_definitions = field_singleton_schema(
            field, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
        )
        definitions.update(f_definitions)
        if f_schema:
            # The dict values are not simply Any
            return {'type': 'object', 'additionalProperties': f_schema}, definitions
        else:
            # The dict values are Any, no need to declare it
            return {'type': 'object'}, definitions
    elif field.shape is Shape.TUPLE:
        sub_schema = []
        for sf in field.sub_fields:
            sf_schema, sf_definitions = field_type_schema(
                sf, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
            )
            definitions.update(sf_definitions)
            sub_schema.append(sf_schema)
        if len(sub_schema) == 1:
            sub_schema = sub_schema[0]
        return {'type': 'array', 'items': sub_schema}, definitions
    else:
        assert field.shape is Shape.SINGLETON, field.shape
        f_schema, f_definitions = field_singleton_schema(
            field,
            by_alias=by_alias,
            model_name_map=model_name_map,
            schema_overrides=schema_overrides,
            ref_prefix=ref_prefix,
        )
        definitions.update(f_definitions)
        return f_schema, definitions


def model_process_schema(
    model: Type['main.BaseModel'], *, by_alias=True, model_name_map: Dict[Type['main.BaseModel'], str], ref_prefix=None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Used by ``model_schema()``, you probably should be using that function.

    Take a single ``model`` and generate its schema. Also return additional schema definitions, from sub-models. The
    sub-models of the returned schema will be referenced, but their definitions will not be included in the schema. All
    the definitions are returned as the second value.
    """
    ref_prefix = ref_prefix or default_prefix
    s = {'title': model.__config__.title or model.__name__}
    if model.__doc__:
        s['description'] = clean_docstring(model.__doc__)
    m_schema, m_definitions = model_type_schema(
        model, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
    )
    s.update(m_schema)
    return s, m_definitions


def model_type_schema(
    model: 'main.BaseModel', *, by_alias: bool, model_name_map: Dict[Type['main.BaseModel'], str], ref_prefix=None
):
    """
    You probably should be using ``model_schema()``, this function is indirectly used by that function.

    Take a single ``model`` and generate the schema for its type only, not including additional
    information as title, etc. Also return additional schema definitions, from sub-models.
    """
    ref_prefix = ref_prefix or default_prefix
    properties = {}
    required = []
    definitions = {}
    for k, f in model.__fields__.items():
        f_schema, f_definitions = field_schema(
            f, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
        )
        definitions.update(f_definitions)
        if by_alias:
            properties[f.alias] = f_schema
            if f.required:
                required.append(f.alias)
        else:
            properties[k] = f_schema
            if f.required:
                required.append(k)
    out_schema = {'type': 'object', 'properties': properties}
    if required:
        out_schema['required'] = required
    return out_schema, definitions


def field_singleton_sub_fields_schema(
    sub_fields: Sequence[Field],
    *,
    by_alias: bool,
    model_name_map: Dict[Type['main.BaseModel'], str],
    schema_overrides=False,
    ref_prefix=None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    This function is indirectly used by ``field_schema()``, you probably should be using that function.

    Take a list of Pydantic ``Field`` from the declaration of a type with parameters, and generate their
    schema. I.e., fields used as "type parameters", like ``str`` and ``int`` in ``Tuple[str, int]``.
    """
    ref_prefix = ref_prefix or default_prefix
    definitions = {}
    if len(sub_fields) == 1:
        return field_type_schema(
            sub_fields[0],
            by_alias=by_alias,
            model_name_map=model_name_map,
            schema_overrides=schema_overrides,
            ref_prefix=ref_prefix,
        )
    else:
        sub_field_schemas = []
        for sf in sub_fields:
            sub_schema, sub_definitions = field_type_schema(
                sf,
                by_alias=by_alias,
                model_name_map=model_name_map,
                schema_overrides=schema_overrides,
                ref_prefix=ref_prefix,
            )
            definitions.update(sub_definitions)
            sub_field_schemas.append(sub_schema)
        return {'anyOf': sub_field_schemas}, definitions


validation_attribute_to_schema_keyword = {
    'min_length': 'minLength',
    'max_length': 'maxLength',
    'regex': 'pattern',
    'gt': 'exclusiveMinimum',
    'lt': 'exclusiveMaximum',
    'ge': 'minimum',
    'le': 'maximum',
}

# Order is important, subclasses of str must go before str, etc
field_class_to_schema_enum_enabled = (
    (EmailStr, {'type': 'string', 'format': 'email'}),
    (UrlStr, {'type': 'string', 'format': 'uri'}),
    (DSN, {'type': 'string', 'format': 'dsn'}),
    (str, {'type': 'string'}),
    (bytes, {'type': 'string', 'format': 'binary'}),
    (bool, {'type': 'boolean'}),
    (int, {'type': 'integer'}),
    (float, {'type': 'number'}),
    (Decimal, {'type': 'number'}),
    (UUID1, {'type': 'string', 'format': 'uuid1'}),
    (UUID3, {'type': 'string', 'format': 'uuid3'}),
    (UUID4, {'type': 'string', 'format': 'uuid4'}),
    (UUID5, {'type': 'string', 'format': 'uuid5'}),
    (UUID, {'type': 'string', 'format': 'uuid'}),
    (NameEmail, {'type': 'string', 'format': 'name-email'}),
)


# Order is important, subclasses of Path must go before Path, etc
field_class_to_schema_enum_disabled = (
    (FilePath, {'type': 'string', 'format': 'file-path'}),
    (DirectoryPath, {'type': 'string', 'format': 'directory-path'}),
    (Path, {'type': 'string', 'format': 'path'}),
    (datetime, {'type': 'string', 'format': 'date-time'}),
    (date, {'type': 'string', 'format': 'date'}),
    (time, {'type': 'string', 'format': 'time'}),
    (timedelta, {'type': 'string', 'format': 'time-delta'}),
    (Json, {'type': 'string', 'format': 'json-string'}),
)


def field_singleton_schema(  # noqa: C901 (ignore complexity)
    field: Field,
    *,
    by_alias: bool,
    model_name_map: Dict[Type['main.BaseModel'], str],
    schema_overrides=False,
    ref_prefix=None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    This function is indirectly used by ``field_schema()``, you should probably be using that function.

    Take a single Pydantic ``Field``, and return its schema and any additional definitions from sub-models.
    """

    ref_prefix = ref_prefix or default_prefix
    definitions = {}
    if field.sub_fields:
        return field_singleton_sub_fields_schema(
            field.sub_fields,
            by_alias=by_alias,
            model_name_map=model_name_map,
            schema_overrides=schema_overrides,
            ref_prefix=ref_prefix,
        )
    if field.type_ is Any:
        return {}, definitions  # no restrictions
    f_schema = {}
    if issubclass(field.type_, Enum):
        f_schema.update({'enum': [item.value for item in field.type_]})
        # Don't return immediately, to allow adding specific types
    for field_name, schema_name in validation_attribute_to_schema_keyword.items():
        field_value = getattr(field.type_, field_name, None)
        if field_value is not None:
            if field_name == 'regex':
                field_value = field_value.pattern
            f_schema[schema_name] = field_value
    for type_, t_schema in field_class_to_schema_enum_enabled:
        if issubclass(field.type_, type_):
            f_schema.update(t_schema)
            break
    # Return schema, with or without enum definitions
    if f_schema:
        return f_schema, definitions
    for type_, t_schema in field_class_to_schema_enum_disabled:
        if issubclass(field.type_, type_):
            return t_schema, definitions
    if issubclass(field.type_, main.BaseModel):
        sub_schema, sub_definitions = model_process_schema(
            field.type_, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
        )
        definitions.update(sub_definitions)
        if not schema_overrides:
            model_name = model_name_map[field.type_]
            definitions[model_name] = sub_schema
            return {'$ref': f'{ref_prefix}{model_name}'}, definitions
        else:
            return sub_schema, definitions
    raise ValueError(f'Value not declarable with JSON Schema, field: {field}')


def encode_default(dft):
    if isinstance(dft, (int, float, str)):
        return dft
    elif isinstance(dft, (tuple, list, set)):
        t = type(dft)
        return t(encode_default(v) for v in dft)
    elif isinstance(dft, dict):
        return {encode_default(k): encode_default(v) for k, v in dft.items()}
    else:
        return pydantic_encoder(dft)
