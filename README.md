# pydantic-core

[![CI](https://github.com/samuelcolvin/pydantic-core/workflows/ci/badge.svg?event=push)](https://github.com/samuelcolvin/pydantic-core/actions?query=event%3Apush+branch%3Amain+workflow%3Aci)
[![Coverage](https://codecov.io/gh/samuelcolvin/pydantic-core/branch/main/graph/badge.svg?token=L2JQIWfqyv)](https://codecov.io/gh/samuelcolvin/pydantic-core)


This package provides the core functionality for pydantic.

The package is currently a work in progress and subject to significant change.

There is, as yet, no integration with pydantic, so schemas can only be defined via dictionaries.

The plan is for pydantic to adopt `pydantic-core` in v2 and to generate the schema definition from type hints in
pydantic, then create a `SchemaValidator` upon model creation.

`pydantic-core` will be a separate package, required by `pydantic`.

The public interface to pydantic shouldn't change too much as a result of this switch
(though I intend to clean up quite a lot in the public API in v2 as well).

Example of usage:

```py
from pydantic_core import SchemaValidator, ValidationError

v = SchemaValidator({
    'title': 'MyModel',
    'type': 'model',
    'fields': {
        'name': {
            'schema': {
                'type': 'str',
            },
        },
        'age': {
            'schema': {
                'type': 'int',
                'ge': 18,
            },
        },
        'is_developer': {
            'schema': {
                'type': 'bool',
            },
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
See [`tests/test_benchmarks.py`](./tests/test_benchmarks.py) for details.

Benchmarks overtime can be seen [here](https://samuelcolvin.github.io/pydantic-core/dev/bench/).

This relative performance will be less impressive for small models but could be significantly move impressive
for deeply nested models.

The improvement will decrease slightly when we have to create a class instance after validation,
but shouldn't change more.

The aim is to remain 10x faster than current pydantic for common use cases.

## Why not JSONSchema?

Looking at the above schema passed to `SchemaValidator` it would seem reasonable to ask "why not use JSONSchema?".

And if we could use JSONSchema, why not use an existing rust library to do validation?

In fact, in the very early commits to pydantic-core, I did try to use JSONSchema,
however I quickly realized it wouldn't work.

JSONSchema does not match the schema for pydantic that closely:
* there are lots of extra checks which pydantic wants to do and aren't covered by JSONSchema
* there are configurations which are possible in JSONSchema but are hard or impossible to imagine in pydantic
* pydantic has the concept of parsing or coercion at it's core, JSONSchema doesn't -
  it assumes you either accept or reject the input, never change it
* There are whole classes of problem pydantic has to deal with (like python class instance validation) which JSONSchema
  has no idea about since it's dedicated to JSON

Even if we could use JSONSchema, it wouldn't help much since rust JSONSchema validators expect to know the
schema at compile time, pydantic-core has no knowledge of the schema until `SchemaValidator` is initialised.

Still, it wouldn't be that hard to implement a conversion layer (either in python or rust) to convert JSONSchema
to "pydantic schema" and thereby achieve partial JSONSchema validation.
