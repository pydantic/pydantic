# pydantic-core

[![CI](https://github.com/samuelcolvin/pydantic-core/workflows/ci/badge.svg?event=push)](https://github.com/samuelcolvin/pydantic-core/actions?query=event%3Apush+branch%3Amain+workflow%3Aci)
[![Coverage](https://codecov.io/gh/samuelcolvin/pydantic-core/branch/main/graph/badge.svg?token=L2JQIWfqyv)](https://codecov.io/gh/samuelcolvin/pydantic-core)


This package provides the core functionality for pydantic.

The package is currently a work in progress and subject to significant change.

There is, as yet, no integration with pydantic, so schemas can only be defined via dictionaries.

The plan is to generate this schema definition from type hints in pydantic, then create a `SchemaValidator`
upon model creation.

`pydantic-core` will be a separate package, required by `pydantic`.

Example of usage:

```py
from pydantic_core import SchemaValidator, ValidationError

v = SchemaValidator({
    'title': 'MyModel',
    'type': 'model',
    'fields': {
        'name': {
            'type': 'str',
        },
        'age': {
            'type': 'int-constrained',
            'ge': 18,
        },
        'is_developer': {
            'type': 'bool',
            'default': True,
        },
    },
})
print(v)
"""
SchemaValidator(title="MyModel", validator=ModelValidator ...
"""

r1 = v.validate_python({'name': 'Samuel', 'age': 35})
print(r1)
"""
(
  {'name': 'Samuel', 'age': 35, 'is_developer': True}, <- validated data
  {'age', 'name'} <- fields set
)
"""

# pydantic-core can also validate JSON directly
r2 = v.validate_json('{"name": "Samuel", "age": 35}')
assert r1 == r2

try:
    v.validate_python({'name': 'Samuel', 'age': 11})
except ValidationError as e:
    print(e)
    """
    1 validation error for MyModel
    age
      Value must be greater than or equal to 18
      [kind=int_greater_than_equal, context={ge: 18}, input_value=11, input_type=int]
    """
```

Pydantic-core is currently around 17x faster than pydantic standard.
See [`benchmarks/run.py`](./benchmarks/run.py) for details.

This relative performance will be less impressive for small models but could be significantly move impressive
for deeply nested models.

The improvement will decrease slightly when we have to create a class instance after validation,
but shouldn't change more.

The aim is to remain 10x faster than current pydantic for common use cases.

The current implementation only deals with parsing/validation of the schema, in future this package could be
used to improve the performance of `.dict()` and `.json()` methods.
