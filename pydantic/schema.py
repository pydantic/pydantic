import re

# from ._generate_schema import generate_config, model_fields_schema
TYPE_MAP = {
    int: 'integer',
    str: 'string',
    list: 'array',
    bool: 'boolean',
    float: 'number',
    None: 'null',
    dict: 'object',
}


def is_required(field_name, field):
    pass


def get_schema_property_json(field_name, field):
    return {
        'title': field_name,
        'type': TYPE_MAP.get(field.annotation, 'object')
    }

    # _property = {}
    # _property['title'] = field.title
    # _property['type'] = TYPE_MAP.get(field.annotation, 'object')
    # # _json_schema['properties'].update(_property)

    # # field.annotation

    # # print(dir(field))
    # # print(field.metadata)
    # # print(field.__gt__)
    # # print()
    # # exit()
    # # property['exclusiveMinimum']

    # # if field.title:
    #     # _json_schema

    # # json_schema_extra
    # # description
    # # title

    # # _json_schema['properties'].update(property)
    # return _json_schema

    # return {'title' 'type'}
    pass


def inner_schema_to_json_schema(inner_schema, fields):
    # print(inner_schema)

    assert inner_schema['type'] == 'typed-dict'

    # Start the JSON Schema document.
    _json_schema_doc = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        # "$id"
        "title": normalize_name(inner_schema['ref'].split('.')[-1]),
        "type": "object",
        "properties": dict(),
        "required": []
    }

    # Update the properites.
    for i, field_name in enumerate(inner_schema['fields']):
        # Get a reference to the field from inner schema, in case we need it later on.
        _inner_schema_field = inner_schema['fields'][field_name]
        _fieldinfo = fields[list(fields.keys())[i]]

        # Update the extracted properties for the field.
        _json_schema_doc['properties'][field_name] = get_schema_property_json(field_name=field_name, field=fields[field_name])

        # If the field is required, let's declare it as so.
        if _fieldinfo.is_required():
            _json_schema_doc["required"].append(field_name)

    return _json_schema_doc


def normalize_name(name: str) -> str:
    """
    Normalizes the given name. This can be applied to either a model *or* enum.
    """
    return re.sub(r'[^a-zA-Z0-9.\-_]', '_', name)


# class SkipField(Exception):
#     """
#     Utility exception used to exclude fields from schema.
#     """

#     def __init__(self, message: str) -> None:
#         self.message = message
