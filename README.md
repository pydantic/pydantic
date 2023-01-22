# pydantic-core

[![CI](https://github.com/pydantic/pydantic-core/workflows/ci/badge.svg?event=push)](https://github.com/pydantic/pydantic-core/actions?query=event%3Apush+branch%3Amain+workflow%3Aci)
[![Coverage](https://codecov.io/gh/pydantic/pydantic-core/branch/main/graph/badge.svg)](https://codecov.io/gh/pydantic/pydantic-core)
[![pypi](https://img.shields.io/pypi/v/pydantic-core.svg)](https://pypi.python.org/pypi/pydantic-core)
[![versions](https://img.shields.io/pypi/pyversions/pydantic-core.svg)](https://github.com/pydantic/pydantic-core)
[![license](https://img.shields.io/github/license/pydantic/pydantic-core.svg)](https://github.com/pydantic/pydantic-core/blob/main/LICENSE)

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
    'type': 'typed-dict',
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
                'type': 'default',
                'schema': {'type': 'bool'},
                'default': True,
            }
        },
    },
})

r1 = v.validate_python({'name': 'Samuel', 'age': 35})
assert r1 == {'name': 'Samuel', 'age': 35, 'is_developer': True}

# pydantic-core can also validate JSON directly
r2 = v.validate_json('{"name": "Samuel", "age": 35}')
assert r1 == r2

try:
    v.validate_python({'name': 'Samuel', 'age': 11})
except ValidationError as e:
    print(e)
    """
    1 validation error for model
    age
      Input should be greater than or equal to 18
      [type=greater_than_equal, context={ge: 18}, input_value=11, input_type=int]
    """
```

Pydantic-core is currently around 17x faster than pydantic standard.
See [`tests/benchmarks/`](./tests/benchmarks/) for details.

This relative performance will be less impressive for small models but could be significantly move impressive
for deeply nested models.

The improvement will decrease slightly when we have to create a class instance after validation,
but shouldn't change more.

The aim is to remain 10x faster than current pydantic for common use cases.

## Getting Started

While pydantic-core is not yet released and not designed for direct use, you can still try it.

You'll need rust stable [installed](https://rustup.rs/), or rust nightly if you want to generate accurate coverage.

With rust and python 3.7+ installed, compiling pydantic-core should be possible with roughly the following:

```bash
# clone this repo or your fork
git clone git@github.com:pydantic/pydantic-core.git
cd pydantic-core
# create a new virtual env
python3 -m venv env
source env/bin/activate
# install dependencies and install pydantic-core
make install
```

That should be it, the example shown above should now run.

You might find it useful to look at [`pydantic_core/_pydantic_core.pyi`](./pydantic_core/_pydantic_core.pyi) and
[`pydantic_core/core_schema.py`](./pydantic_core/core_schema.py) for more information on the python API,
beyond that, [`tests/`](./tests) provide a large number of examples of usage.

If you want to contribute to pydantic-core, you'll want to use some other make commands:
* `make build-dev` to build the package during development
* `make build-prod` to perform an optimised build for benchmarking
* `make test` to run the tests
* `make testcov` to run the tests and generate a coverage report
* `make lint` to run the linter
* `make format` to format python and rust code
* `make` to run `format build-dev lint test`

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
