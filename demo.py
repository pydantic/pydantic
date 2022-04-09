from pydantic_core import SchemaValidator
from devtools import debug

v = SchemaValidator({
    'type': 'model',
    'fields': {
        'name': {
            'type': 'str',
            'required': True,
        },
        'age': {
            'type': 'int',
        },
        'friends': {
            'type': 'list',
            'items': {
                'type': 'int',
            },
        },
    },
})

r = v.validate({'name': 'John', 'age': 42, 'friends': [1, 2, 3]})
debug(r)
r = v.validate({'name': 'John', 'age': 42, 'friends': [1, 2, '3']})
debug(r)
