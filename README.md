# pydantic-core

[![CI](https://github.com/pydantic/pydantic-core/workflows/ci/badge.svg?event=push)](https://github.com/pydantic/pydantic-core/actions?query=event%3Apush+branch%3Amain+workflow%3Aci)
[![Coverage](https://codecov.io/gh/pydantic/pydantic-core/branch/main/graph/badge.svg)](https://codecov.io/gh/pydantic/pydantic-core)
[![pypi](https://img.shields.io/pypi/v/pydantic-core.svg)](https://pypi.python.org/pypi/pydantic-core)
[![versions](https://img.shields.io/pypi/pyversions/pydantic-core.svg)](https://github.com/pydantic/pydantic-core)
[![license](https://img.shields.io/github/license/pydantic/pydantic-core.svg)](https://github.com/pydantic/pydantic-core/blob/main/LICENSE)

This package provides the core functionality for [pydantic](https://docs.pydantic.dev) validation and serialization.

Pydantic-core is currently around 17x faster than pydantic V1.
See [`tests/benchmarks/`](./tests/benchmarks/) for details.

## Example of direct usage

_NOTE: You should not need to use pydantic-core directly; instead, use pydantic, which in turn uses pydantic-core._

```py
from pydantic_core import SchemaValidator, ValidationError


v = SchemaValidator(
    {
        'type': 'typed-dict',
        'fields': {
            'name': {
                'type': 'typed-dict-field',
                'schema': {
                    'type': 'str',
                },
            },
            'age': {
                'type': 'typed-dict-field',
                'schema': {
                    'type': 'int',
                    'ge': 18,
                },
            },
            'is_developer': {
                'type': 'typed-dict-field',
                'schema': {
                    'type': 'default',
                    'schema': {'type': 'bool'},
                    'default': True,
                },
            },
        },
    }
)

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

## Getting Started

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

You might find it useful to look at [`python/pydantic_core/_pydantic_core.pyi`](./python/pydantic_core/_pydantic_core.pyi) and
[`python/pydantic_core/core_schema.py`](./python/pydantic_core/core_schema.py) for more information on the python API,
beyond that, [`tests/`](./tests) provide a large number of examples of usage.

If you want to contribute to pydantic-core, you'll want to use some other make commands:
* `make build-dev` to build the package during development
* `make build-prod` to perform an optimised build for benchmarking
* `make test` to run the tests
* `make testcov` to run the tests and generate a coverage report
* `make lint` to run the linter
* `make format` to format python and rust code
* `make` to run `format build-dev lint test`
