from pydantic_core import SchemaValidator, ValidationError
from devtools import debug

v = SchemaValidator({
    'title': 'MyTestModel',
    'type': 'model',
    'fields': {
        'name': {
            'type': 'str',
        },
        'age': {
            'type': 'int-constrained',
            'ge': 18,
        },
        'is_employer': {
            'type': 'bool',
            'default': True,
        },
        'friends': {
            'type': 'list',
            'items': {
                'type': 'int',
                'gt': 0,
            },
        },
        'settings': {
            'type': 'dict',
            'keys': {
                'type': 'str',
            },
            'values': {
                'type': 'float',
            }
        }
    },
})
print(repr(v))

r = v.validate_python({'name': 'John', 'age': 42, 'friends': [1, 2, 3], 'settings': {'a': 1.0, 'b': 2.0}})
debug(r)

try:
    r = v.validate_python({'name': 'John', 'age': 16, 'friends': [-1, 2, 3, -1], 'settings': {'a': 1.0, 'b': 2.0}})
except ValidationError as e:
    print(e)
