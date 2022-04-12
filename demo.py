from pydantic_core import SchemaValidator
from devtools import debug
v = SchemaValidator({
    'model_name': 'MyTestModel',
    'type': 'model',
    'fields': {
        'age': {
            'type': 'int-constrained',
            'ge': 'not-int',
        },
    },
})
v = SchemaValidator({
    'model_name': 'MyTestModel',
    'type': 'model',
    'fields': {
        'name': {
            'type': 'str',
            'required': True,
        },
        'age': {
            'type': 'int-constrained',
            'ge': 18,
        },
        'is_employer': {
            'type': 'bool',
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
# print(v)

r = v.run({'name': 'John', 'age': 42, 'is_employer': 'true', 'friends': [1, 2, 3], 'settings': {'a': 1.0, 'b': 2.0}})
debug(r)

r = v.run({'name': 'John', 'age': 16, 'friends': [-1, 2, 3, -1], 'settings': {'a': 1.0, 'b': 2.0}})
debug(r)
