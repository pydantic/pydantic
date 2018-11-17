from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Dict
from uuid import UUID

from . import main
from .fields import Field, Shape
from .types import DSN, UUID1, UUID3, UUID4, UUID5, DirectoryPath, EmailStr, FilePath, Json, NameEmail, UrlStr
from .utils import clean_docstring


def field_schema(field: Field, by_alias=True):
    s = dict(title=field._schema.title or field.alias.title())

    if not field.required and field.default is not None:
        s['default'] = field.default
    s.update(field._schema.extra)

    ts = field_type_schema(field, by_alias)
    s.update(ts)
    return s


def field_type_schema(field: Field, by_alias: bool):
    if field.shape is Shape.LIST:
        return {'type': 'array', 'items': field_singleton_schema(field, by_alias)}
    elif field.shape is Shape.SET:
        return {
            'type': 'array',
            'uniqueItems': True,
            'items': field_singleton_schema(field, by_alias),
        }
    elif field.shape is Shape.MAPPING:
        sub_field_schema = field_singleton_schema(field, by_alias)
        if sub_field_schema:
            # The dict values are not simply Any
            return {
                'type': 'object',
                'additionalProperties': sub_field_schema,
            }
        else:
            # The dict values are Any, no need to declare it
            return {
                'type': 'object'
            }
    elif field.shape is Shape.TUPLE:
        sub_schema = [field_type_schema(sf, by_alias) for sf in field.sub_fields]
        if len(sub_schema) == 1:
            sub_schema = sub_schema[0]
        return {
            'type': 'array',
            'items': sub_schema,
        }
    else:
        assert field.shape is Shape.SINGLETON, field.shape
        return field_singleton_schema(field, by_alias)


def model_schema(class_: 'main.BaseModel', by_alias=True) -> Dict[str, Any]:
    s = {'title': class_.__config__.title or class_.__name__}
    if class_.__doc__:
        s['description'] = clean_docstring(class_.__doc__)

    s.update(model_type_schema(class_, by_alias))
    return s


def model_type_schema(class_: 'main.BaseModel', by_alias: bool):
    if by_alias:
        properties = {f.alias: field_schema(f, by_alias) for f in class_.__fields__.values()}
        required = [f.alias for f in class_.__fields__.values() if f.required]
    else:
        properties = {k: field_schema(f, by_alias) for k, f in class_.__fields__.items()}
        required = [k for k, f in class_.__fields__.items() if f.required]
    out_schema = {'type': 'object', 'properties': properties}
    if required:
        out_schema['required'] = required
    return out_schema


def field_singleton_schema(field: Field, by_alias: bool):
    if field.sub_fields:
        if len(field.sub_fields) == 1:
            return field_type_schema(field.sub_fields[0], by_alias)
        else:
            return {'anyOf': [field_type_schema(sf, by_alias) for sf in field.sub_fields]}
    if field.type_ is Any:
        return {}  # no restrictions
    schema_value = {}
    if issubclass(field.type_, Enum):
        schema_value.update({'enum': [item.value for item in field.type_]})
        # Don't return immediately, to allow adding specific types
    # For constrained strings
    if hasattr(field.type_, 'min_length'):
        if field.type_.min_length is not None:
            schema_value.update({'minLength': field.type_.min_length})
    if hasattr(field.type_, 'max_length'):
        if field.type_.max_length is not None:
            schema_value.update({'maxLength': field.type_.max_length})
    if hasattr(field.type_, 'regex'):
        if field.type_.regex is not None:
            schema_value.update({'pattern': field.type_.regex.pattern})
    # For constrained numbers
    if hasattr(field.type_, 'gt'):
        if field.type_.gt is not None:
            schema_value.update({'exclusiveMinimum': field.type_.gt})
    if hasattr(field.type_, 'lt'):
        if field.type_.lt is not None:
            schema_value.update({'exclusiveMaximum': field.type_.lt})
    if hasattr(field.type_, 'ge'):
        if field.type_.ge is not None:
            schema_value.update({'minimum': field.type_.ge})
    if hasattr(field.type_, 'le'):
        if field.type_.le is not None:
            schema_value.update({'maximum': field.type_.le})
    # Sub-classes of str must go before str
    if issubclass(field.type_, EmailStr):
        schema_value.update({'type': 'string', 'format': 'email'})
        return schema_value
    if issubclass(field.type_, UrlStr):
        schema_value.update({'type': 'string', 'format': 'uri'})
        return schema_value
    if issubclass(field.type_, DSN):
        schema_value.update({'type': 'string', 'format': 'dsn'})
        return schema_value
    if issubclass(field.type_, str):
        schema_value.update({'type': 'string'})
        return schema_value
    elif issubclass(field.type_, bytes):
        schema_value.update({'type': 'string', 'format': 'binary'})
        return schema_value
    elif issubclass(field.type_, bool):
        schema_value.update({'type': 'boolean'})
        return schema_value
    elif issubclass(field.type_, int):
        schema_value.update({'type': 'integer'})
        return schema_value
    elif issubclass(field.type_, float):
        schema_value.update({'type': 'number'})
        return schema_value
    elif issubclass(field.type_, Decimal):
        schema_value.update({'type': 'number'})
        return schema_value
    elif issubclass(field.type_, UUID1):
        schema_value.update({'type': 'string', 'format': 'uuid1'})
        return schema_value
    elif issubclass(field.type_, UUID3):
        schema_value.update({'type': 'string', 'format': 'uuid3'})
        return schema_value
    elif issubclass(field.type_, UUID4):
        schema_value.update({'type': 'string', 'format': 'uuid4'})
        return schema_value
    elif issubclass(field.type_, UUID5):
        schema_value.update({'type': 'string', 'format': 'uuid5'})
        return schema_value
    elif issubclass(field.type_, UUID):
        schema_value.update({'type': 'string', 'format': 'uuid'})
        return schema_value
    elif issubclass(field.type_, NameEmail):
        schema_value.update({'type': 'string', 'format': 'name-email'})
        return schema_value
        # This is the last value that can also be an Enum
    if schema_value:
        return schema_value
    # Path subclasses must go before Path
    elif issubclass(field.type_, FilePath):
        return {'type': 'string', 'format': 'file-path'}
    elif issubclass(field.type_, DirectoryPath):
        return {'type': 'string', 'format': 'directory-path'}
    elif issubclass(field.type_, Path):
        return {'type': 'string', 'format': 'path'}
    elif issubclass(field.type_, datetime):
        return {'type': 'string', 'format': 'date-time'}
    elif issubclass(field.type_, date):
        return {'type': 'string', 'format': 'date'}
    elif issubclass(field.type_, time):
        return {'type': 'string', 'format': 'time'}
    elif issubclass(field.type_, timedelta):
        return {'type': 'string', 'format': 'time-delta'}
    elif issubclass(field.type_, Json):
        return {'type': 'string', 'format': 'json-string'}
    elif issubclass(field.type_, main.BaseModel):
        return model_schema(field.type_, by_alias)
    raise ValueError('Value not declarable with JSON Schema')
