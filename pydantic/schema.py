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


def get_flat_models_from_model(model: Type['main.BaseModel']) -> Set[Type['main.BaseModel']]:
    flat_models: Set[Type[main.BaseModel]] = set()
    assert issubclass(model, main.BaseModel)
    flat_models.add(model)
    for field in model.__fields__.values():
        flat_models = flat_models | get_flat_models_from_field(field)
    return flat_models


def get_flat_models_from_field(field: Field) -> Set[Type['main.BaseModel']]:
    flat_models: Set[Type[main.BaseModel]] = set()
    if field.sub_fields:
        flat_models = flat_models | get_flat_models_from_sub_fields(field.sub_fields)
    elif isinstance(field.type_, type) and issubclass(field.type_, main.BaseModel):
        flat_models = flat_models | get_flat_models_from_model(field.type_)
    return flat_models


def get_flat_models_from_sub_fields(fields) -> Set[Type['main.BaseModel']]:
    flat_models: Set[Type[main.BaseModel]] = set()
    for field in fields:
        flat_models = flat_models | get_flat_models_from_field(field)
    return flat_models


def get_flat_models_from_models(models: Sequence[Type['main.BaseModel']]) -> Set[Type['main.BaseModel']]:
    flat_models: Set[Type[main.BaseModel]] = set()
    for model in models:
        flat_models = flat_models | get_flat_models_from_model(model)
    return flat_models


def get_long_model_name(model: Type['main.BaseModel']):
    assert issubclass(model, main.BaseModel)
    prefix = model.__module__.replace('.', '__')
    name = model.__name__
    return f'{prefix}__{name}'


def get_model_name_maps(
    unique_models: Set[Type['main.BaseModel']]
) -> Tuple[Dict[str, Type['main.BaseModel']], Dict[Type['main.BaseModel'], str]]:
    name_model_map: Dict[str, Type[main.BaseModel]] = {}
    conflicting_names: Set[str] = set()
    for model in unique_models:
        model_name = model.__name__
        if model_name in conflicting_names:
            model_name = get_long_model_name(model)
            name_model_map[model_name] = model
        elif model_name in name_model_map:
            conflicting_names.add(model_name)
            conflicting_model = name_model_map[model_name]
            del name_model_map[model_name]
            conflicting_model_name = get_long_model_name(conflicting_model)
            name_model_map[conflicting_model_name] = conflicting_model
            model_name = get_long_model_name(model)
            name_model_map[model_name] = model
        else:
            name_model_map[model_name] = model
    model_name_map = {v: k for k, v in name_model_map.items()}
    return name_model_map, model_name_map


def field_schema(
    field: Field, *, by_alias=True, model_name_map: Dict[Type['main.BaseModel'], str], ref_prefix='#/definitions/'
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    schema_overrides = False
    s = dict(title=field._schema.title or field.alias.title())
    if field._schema.title:
        schema_overrides = True

    if not field.required and field.default is not None:
        schema_overrides = True
        if isinstance(field.default, (int, float, bool, str)):
            s['default'] = field.default
        else:
            s['default'] = pydantic_encoder(field.default)
    if field._schema.extra:
        s.update(field._schema.extra)
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


def field_type_schema(
    field: Field,
    *,
    by_alias: bool,
    model_name_map: Dict[Type['main.BaseModel'], str],
    schema_overrides=False,
    ref_prefix='#/definitions/',
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    definitions = {}
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
    class_: Type['main.BaseModel'],
    *,
    by_alias=True,
    model_name_map: Dict[Type['main.BaseModel'], str],
    ref_prefix='#/definitions/',
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    s = {'title': class_.__config__.title or class_.__name__}
    if class_.__doc__:
        s['description'] = clean_docstring(class_.__doc__)
    m_schema, m_definitions = model_type_schema(
        class_, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
    )
    s.update(m_schema)
    return s, m_definitions


def model_type_schema(
    class_: 'main.BaseModel',
    *,
    by_alias: bool,
    model_name_map: Dict[Type['main.BaseModel'], str],
    ref_prefix='#/definitions/',
):
    properties = {}
    required = []
    definitions = {}
    for k, f in class_.__fields__.items():
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
    ref_prefix='#/definitions/',
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
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


def field_singleton_schema(  # noqa: C901 (ignore complexity)
    field: Field,
    *,
    by_alias: bool,
    model_name_map: Dict[Type['main.BaseModel'], str],
    schema_overrides=False,
    ref_prefix='#/definitions/',
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
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
    # For constrained strings
    if hasattr(field.type_, 'min_length'):
        if field.type_.min_length is not None:
            f_schema.update({'minLength': field.type_.min_length})
    if hasattr(field.type_, 'max_length'):
        if field.type_.max_length is not None:
            f_schema.update({'maxLength': field.type_.max_length})
    if hasattr(field.type_, 'regex'):
        if field.type_.regex is not None:
            f_schema.update({'pattern': field.type_.regex.pattern})
    # For constrained numbers
    if hasattr(field.type_, 'gt'):
        if field.type_.gt is not None:
            f_schema.update({'exclusiveMinimum': field.type_.gt})
    if hasattr(field.type_, 'lt'):
        if field.type_.lt is not None:
            f_schema.update({'exclusiveMaximum': field.type_.lt})
    if hasattr(field.type_, 'ge'):
        if field.type_.ge is not None:
            f_schema.update({'minimum': field.type_.ge})
    if hasattr(field.type_, 'le'):
        if field.type_.le is not None:
            f_schema.update({'maximum': field.type_.le})
    # Sub-classes of str must go before str
    if issubclass(field.type_, EmailStr):
        f_schema.update({'type': 'string', 'format': 'email'})
    elif issubclass(field.type_, UrlStr):
        f_schema.update({'type': 'string', 'format': 'uri'})
    elif issubclass(field.type_, DSN):
        f_schema.update({'type': 'string', 'format': 'dsn'})
    elif issubclass(field.type_, str):
        f_schema.update({'type': 'string'})
    elif issubclass(field.type_, bytes):
        f_schema.update({'type': 'string', 'format': 'binary'})
    elif issubclass(field.type_, bool):
        f_schema.update({'type': 'boolean'})
    elif issubclass(field.type_, int):
        f_schema.update({'type': 'integer'})
    elif issubclass(field.type_, float):
        f_schema.update({'type': 'number'})
    elif issubclass(field.type_, Decimal):
        f_schema.update({'type': 'number'})
    elif issubclass(field.type_, UUID1):
        f_schema.update({'type': 'string', 'format': 'uuid1'})
    elif issubclass(field.type_, UUID3):
        f_schema.update({'type': 'string', 'format': 'uuid3'})
    elif issubclass(field.type_, UUID4):
        f_schema.update({'type': 'string', 'format': 'uuid4'})
    elif issubclass(field.type_, UUID5):
        f_schema.update({'type': 'string', 'format': 'uuid5'})
    elif issubclass(field.type_, UUID):
        f_schema.update({'type': 'string', 'format': 'uuid'})
    elif issubclass(field.type_, NameEmail):
        f_schema.update({'type': 'string', 'format': 'name-email'})
        # This is the last value that can also be an Enum
    if f_schema:
        return f_schema, definitions
    # Path subclasses must go before Path
    elif issubclass(field.type_, FilePath):
        return {'type': 'string', 'format': 'file-path'}, definitions
    elif issubclass(field.type_, DirectoryPath):
        return {'type': 'string', 'format': 'directory-path'}, definitions
    elif issubclass(field.type_, Path):
        return {'type': 'string', 'format': 'path'}, definitions
    elif issubclass(field.type_, datetime):
        return {'type': 'string', 'format': 'date-time'}, definitions
    elif issubclass(field.type_, date):
        return {'type': 'string', 'format': 'date'}, definitions
    elif issubclass(field.type_, time):
        return {'type': 'string', 'format': 'time'}, definitions
    elif issubclass(field.type_, timedelta):
        return {'type': 'string', 'format': 'time-delta'}, definitions
    elif issubclass(field.type_, Json):
        return {'type': 'string', 'format': 'json-string'}, definitions
    elif issubclass(field.type_, main.BaseModel):
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
    raise ValueError('Value not declarable with JSON Schema')


def model_schema(class_: 'main.BaseModel', by_alias=True, ref_prefix='#/definitions/') -> Dict[str, Any]:
    flat_models = get_flat_models_from_model(class_)
    _, model_name_map = get_model_name_maps(flat_models)
    m_schema, m_definitions = model_process_schema(
        class_, by_alias=by_alias, model_name_map=model_name_map, ref_prefix=ref_prefix
    )
    if m_definitions:
        m_schema.update({'definitions': m_definitions})
    return m_schema


def schema(
    models: Sequence[Type['main.BaseModel']],
    *,
    by_alias=True,
    title=None,
    description=None,
    ref_prefix='#/definitions/',
) -> Dict:
    flat_models = get_flat_models_from_models(models)
    _, model_name_map = get_model_name_maps(flat_models)
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
