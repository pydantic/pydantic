from genson import SchemaBuilder

# from ._generate_schema import generate_config, model_fields_schema
TYPE_MAP = {
    int: 'integer',
    str: 'string',
    list: 'array',
    bool: 'boolean',
    float: 'number',
    None: 'null',
    dict: 'object'

}

def get_field_json(field_name, field):
    # print(locals())
    _json_schema = {
        "properties": {},
        "required": []
    }

    if field.is_required():
        _json_schema['required'].append(field_name)

    property = {}
    property['title'] = field.title
    property['type'] = TYPE_MAP.get(field.annotation)


    field.annotation

    print(field)
    print()
    # exit()
    # property['exclusiveMinimum']

    if field.title:
        _json_schema

    # json_schema_extra
    # description
    # title

    _json_schema['properties'].update(property)
    return _json_schema

def inner_schema_to_json_schema(inner_schema, fields):
    # TODO: additional params
    # from pprint import pprint
    # pprint(locals())
    # fields = None
    print(inner_schema)

    # print(inner_schema)
    assert inner_schema['type'] == 'typed-dict'


    # Start the JSON Schema document.
    _json_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        # "$id"
        # "title": "test",
        "type": "object",
        "properties": {},
        "required": []
    }

    # Update the properites.
    for field_name in fields:
        _new_json_schema = get_field_json(field_name=field_name, field=fields[field_name])

        # Update the properies for the under-construction JSON Schema.
        if _new_json_schema["properties"]:
            _json_schema["properties"].update(_new_json_schema["properties"])

        # Update required for the under-construction JSON Schema.
        if _new_json_schema["required"]:
            _json_schema["required"].extend(_new_json_schema["required"])

    return _json_schema


def normalize_name(name: str) -> str:
    """
    Normalizes the given name. This can be applied to either a model *or* enum.
    """
    return re.sub(r'[^a-zA-Z0-9.\-_]', '_', name)


class SkipField(Exception):
    """
    Utility exception used to exclude fields from schema.
    """

    def __init__(self, message: str) -> None:
        self.message = message
