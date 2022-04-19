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
from pydantic_core import SchemaValidator
from devtools import debug

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
        'is_employer': {
            'type': 'bool',
            'default': True,
        },
    },
})
print(repr(v))

r = v.validate_python({'name': 'John', 'age': 42})
debug(r)
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
