import re
import typing
from typing import Any, Dict

# from ._generate_schema import generate_config, model_fields_schema
TYPE_MAP = {
    # Build-ins.
    # int: 'number',
    # str: 'string',
    # list: 'array',
    # bool: 'boolean',
    # float: 'number',
    # None: 'null',
    # dict: 'object',
    'new-class': 'object',
    'datetime': 'date-time',
    'str': 'string',
    'int': 'number',
}

DEFAULT_JSON_SCHEMA_URI = 'https://json-schema.org/draft/2020-12/schema'
DEFAULT_JSON_SCHEMA_PREFIX = '#/definitions/'
DEFAULT_JSON_SCHEMA_REF_TEMPLATE = '#/definitions/{model}'


def internal_to_json_types(s: str) -> str:
    return TYPE_MAP.get(s, s)


def get_schema_property_json(field_name: str, inner_schema_field: Dict[str, Any]):
    """
    Returns a dict, used to construct JSON Schema for a given field's properties.
    """

    declared_type = inner_schema_field['schema']['type']
    _types = []

    # Support for nullables.
    if declared_type == 'nullable':
        t = inner_schema_field['schema']['schema']['type']
        _types.append(internal_to_json_types(t))
        _types.append('null')
    else:
        _types.append(internal_to_json_types(declared_type))

    # If only one type was found, shorten it.
    _types = _types[0] if len(_types) == 1 else _types

    return {'title': normalize_name(field_name), 'type': _types}


def internal_to_json_schema(inner_schema: typing.Dict[str, Any], fields) -> Dict[str, Any]:
    """Returns a JSON Schema document, compatible with draft 2020-12."""

    # print(inner_schema)

    # Sanity check.
    assert inner_schema['type'] == 'typed-dict'

    # Start the JSON Schema document.
    json_schema_doc = {
        '$schema': DEFAULT_JSON_SCHEMA_URI,
        # "$id"
        'title': normalize_name(inner_schema['ref'].split('.')[-1]),
        'type': 'object',
        'properties': {},
        'required': [],
    }

    # Update the properites.
    for i, field_name in enumerate(inner_schema['fields']):

        # Get a reference to the fields from inner schema,
        # in case we need it in development.
        inner_schema_field = inner_schema['fields'][field_name]
        field = fields[list(fields.keys())[i]]

        # Update the extracted properties for the field.
        json_schema_doc['properties'][field_name] = get_schema_property_json(
            field_name=field_name, inner_schema_field=inner_schema_field
        )

        # If the field is required, let's declare it as so.
        if field.is_required():
            json_schema_doc['required'].append(normalize_name(field_name))

    return json_schema_doc


def normalize_name(name: str) -> str:
    """
    Normalizes the given name. This can be applied to either a model *or* enum.
    """
    return re.sub(r'[^a-zA-Z0-9.\-_]', '_', name)
