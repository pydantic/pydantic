"""Notes / TODO:

- No support for (e.g. "multipleOf" : 10), as of yet, as this doesn't appear to
    be included in the pydantic-core schema.
- Support must be added for class Config e.g. schema_extra:

    class Example(BaseModel):
        id: int = 123

        class Config:
            schema_extra = {
                'example': {
                    'id': 123
                }
            }


"""
import re
from typing import Any, Dict, Tuple, Optional

# For reference, (type, format) pairs for converting between
#   Pydantic-Core Schema types to JSON Schema.
TYPE_MAP: Dict[str, Tuple[str, Optional[str]]] = {
    # Build-ins.
    'str': ('string', None),
    'int': ('number', None),
    'float': ('number', None),
    'bool': ('boolean', None),
    'list': ('array', None),
    'None': ('null', None),
    'dict': ('object', None),
    'model': ('object', None),
    'datetime': ('string', 'date-time'),
    'time': ('string', 'time'),
    'date': ('string', 'date'),
    'timedelta': ('number', 'time-delta'),
    'Decimal': ('number', None),
    'UUID': ('string', 'uuid'),
    'Path': ('string', 'path'),
    # 'bytes': ('string', 'binary'),
    # 'Pattern': ('string', 'regex'),
    # 'IPv4Network': ('string', 'ipv4network'),
    # 'IPv6Network': ('string', 'ipv6network'),
    # 'IPv4Interface': ('string', 'ipv4interface'),
    # 'IPv6Interface': ('string', 'ipv6interface'),
    # 'IPv4Address': ('string', 'ipv4'),
    # 'IPv6Address': ('string', 'ipv6'),

    # 'EmailStr': ('string', 'email'),
    # 'UrlStr': ('string', 'url'),
    # 'NameEmail': ('string', 'name-email'),
    # 'PyObject': ('string', 'python-object'),
    # 'Json': ('string', 'json'),
}

DEFAULT_JSON_SCHEMA_URI = 'https://json-schema.org/draft/2020-12/schema'
DEFAULT_JSON_SCHEMA_REF_PREFIX = '#/definitions/'
DEFAULT_JSON_SCHEMA_REF_TEMPLATE = '{model}'

# if typing.TYPE_CHECKING:
#     Model = typing.TypeVar('Model', bound='BaseModel')

def internal_to_json_types(s: str) -> str:
    return TYPE_MAP.get(s, [s])[0]


def internal_to_json_type_format(s: str) -> str:
    return TYPE_MAP.get(s, [s])[1]


def generate_schema(
    # models: Sequence[Union[Type['BaseModel'], Type['Dataclass']]],
    models,
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
    # :param by_alias: generate the schemas using the aliases defined, if any
    # :param title: title for the generated schema that includes the definitions
    # :param description: description for the generated schema
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

    definitions = {}
    for model in models:
        definitions.update(get_model_definitions(model, by_alias=by_alias, ref_prefix=ref_prefix, ref_template=ref_template))

    schema = {
        '$schema': DEFAULT_JSON_SCHEMA_URI,
        'definitions': definitions,
    }
    if title:
        schema['title'] = title
    if description:
        schema['description'] = description
    return schema

def get_schema_property_json(field_name: str, inner_schema_field: Dict[str, Any], *, ref_prefix: str = DEFAULT_JSON_SCHEMA_REF_PREFIX,  ref_template: str = DEFAULT_JSON_SCHEMA_REF_TEMPLATE):
    """
    Returns a dict, used to construct JSON Schema for a given field's properties.
    """

    declared_type = inner_schema_field['schema']['type']
    types = []
    items = []

    is_reference = False

    # Support for nullables.
    if declared_type == 'nullable':
        t = inner_schema_field['schema']['schema']['type']
        types.append(internal_to_json_types(t))
        types.append('null')
    else:
        types.append(internal_to_json_types(declared_type))

    # Support for new classes.
    if declared_type == 'new-class':
        declared_type = 'object'
        is_reference = True

    # Support for typed arrays, which appear in JSON Schema as:
    #    "items": {"type": "number"}
    if 'items_schema' in inner_schema_field['schema']:
        items_schema = inner_schema_field['schema']['items_schema']['type']
        items_schema = internal_to_json_types(items_schema)
        items.append(items_schema)


    # Support for references.
    if is_reference:
        # Add the reference.
        ref = ref_template.format(model=normalize_name(inner_schema_field['schema']['cls'].__name__))
        if ref_prefix:
            ref = ref_prefix + ref
        properties = {'$ref': ref}

    else:
        # Prepare the final dictionary.
        properties = {'title': normalize_name(field_name)}

        # If only one type was found, shorten it (not an array).
        properties['type'] = types[0] if len(types) == 1 else types

        # Include typed array support.
        if items:
            properties['items'] = {'type': items}

    return properties



# TODO: ref prefix from config
# ref_template='foobar/{model}.json'
def internal_to_json_schema(inner_schema: Dict[str, Any], fields, *, config, ref_prefix=DEFAULT_JSON_SCHEMA_REF_PREFIX,  ref_template=DEFAULT_JSON_SCHEMA_REF_TEMPLATE) -> Dict[str, Any]:
    """Returns a JSON Schema document, compatible with draft 2020-12."""

    # Sanity check.
    assert inner_schema['type'] == 'typed-dict'

    model_name = normalize_name(inner_schema['ref'].split('.')[-1])

    # Set the reference prefix.
    schema = DEFAULT_JSON_SCHEMA_URI
    ref = ref_prefix + ref_template.format(model=model_name)

    # Start the JSON Schema document.
    json_schema_doc = {
        '$schema': schema,
        "$ref": ref,
        'title': config.title,
        'type': 'object',
        'properties': {},
        'required': [],
        'definitions': dict(),
    }
    json_schema_defines = {}

    # Iterate over the fields and add them to the JSON Schema document.
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

        # If the field is a reference to another model, let's add it to the definitions.
        if 'cls' in inner_schema_field['schema']:
            class_name = inner_schema_field['schema']['cls'].__name__
            class_ref = inner_schema_field['schema']['cls']

            json_schema_defines[class_name] = class_ref
            json_schema_defines[class_name] = get_schema_property_json(field_name, inner_schema_field=inner_schema_field, ref_prefix=ref_prefix, ref_template=ref_template)

    # if json_schema_defines:
    json_schema_doc['definitions'] = json_schema_defines

    # Return the JSON Schema document.
    return json_schema_doc


def normalize_name(name: str) -> str:
    """
    Normalizes the given name. This can be applied to either a model *or* enum.
    """
    return re.sub(r'[^a-zA-Z0-9.\-_]', '_', name)
