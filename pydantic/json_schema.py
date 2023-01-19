import re
import typing
from typing import Any, Dict, List, Sequence, Union, Type, Optional

# from ._generate_schema import generate_config, model_fields_schema
TYPE_MAP = {
    # Build-ins.
    # int: 'number',
    # str: 'string',
    'list': 'array',
    # bool: 'boolean',
    # float: 'number',
    # None: 'null',
    'dict': 'object',
    'new-class': 'object',
    'datetime': 'date-time',
    'str': 'string',
    'int': 'number',
}

DEFAULT_JSON_SCHEMA_URI = 'https://json-schema.org/draft/2020-12/schema'
DEFAULT_JSON_SCHEMA_REF_PREFIX = '#/definitions/'
DEFAULT_JSON_SCHEMA_REF_TEMPLATE = '#/definitions/{model}'

if typing.TYPE_CHECKING:
    Model = typing.TypeVar('Model', bound='BaseModel')


def internal_to_json_types(s: str) -> str:
    return TYPE_MAP.get(s, s)


def generate_schema(
    models: Sequence[Union[Type['BaseModel'], Type['Dataclass']]],
    *,
    by_alias: bool = True,
    title: Optional[str] = None,
    description: Optional[str] = None,
    ref_prefix: Optional[str] = None,
    ref_template: str = DEFAULT_JSON_SCHEMA_REF_TEMPLATE,
) -> Dict[str, Any]:
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
    :param ref_template: Use a ``string.format()`` template for ``$ref`` instead of a prefix. This can be useful
      for references that cannot be represented by ``ref_prefix`` such as a definition stored in another file. For
      a sibling json file in a ``/schemas`` directory use ``"/schemas/${model}.json#"``.
    :return: dict with the JSON Schema with a ``definitions`` top-level key including the schema definitions for
      the models and sub-models passed in ``models``.
    """

    if ref_prefix is None:
        ref_prefix = DEFAULT_JSON_SCHEMA_PREFIX

    # TODO: implement.
    pass


def get_schema_property_json(field_name: str, inner_schema_field: Dict[str, Any]):
    """
    Returns a dict, used to construct JSON Schema for a given field's properties.
    """

    declared_type = inner_schema_field['schema']['type']
    types = []
    items = []

    # Support for nullables.
    if declared_type == 'nullable':
        t = inner_schema_field['schema']['schema']['type']
        types.append(internal_to_json_types(t))
        types.append('null')
    else:
        types.append(internal_to_json_types(declared_type))



    # Support for typed arrays, which appear in JSON Schema as:
    #    "items": {"type": "number"}
    if 'items_schema' in inner_schema_field['schema']:
        items_schema = inner_schema_field['schema']['items_schema']['type']
        items_schema = internal_to_json_types(items_schema)
        items.append(items_schema)

    # Prepare the final dictionary.
    properties = {'title': normalize_name(field_name)}
    # If only one type was found, shorten it (not an array).
    properties['type'] = types[0] if len(types) == 1 else types

    # Include typed array support.
    if items:
        properties['items'] = {'type': items}

    return properties


def internal_to_json_schema(inner_schema: Dict[str, Any], fields) -> Dict[str, Any]:
    """Returns a JSON Schema document, compatible with draft 2020-12."""

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
