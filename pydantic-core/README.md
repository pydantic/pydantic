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

### Prerequisites

You'll need:
1. **[Rust](https://rustup.rs/)** - Rust stable (or nightly for coverage)
2. **[uv](https://docs.astral.sh/uv/getting-started/installation/)** - Fast Python package manager (will install Python 3.9+ automatically)
3. **[git](https://git-scm.com/)** - For version control
4. **[make](https://www.gnu.org/software/make/)** - For running development commands (or use `nmake` on Windows)

### Quick Start

```bash
# Clone the repository (or from your fork)
git clone git@github.com:pydantic/pydantic-core.git
cd pydantic-core

# Install all dependencies using uv, setup pre-commit hooks, and build the development version
make install
```

Verify your installation by running:

```bash
make
```

This runs a full development cycle: formatting, building, linting, and testing

### Development Commands

Run `make help` to see all available commands, or use these common ones:

```bash
make build-dev    # to build the package during development
make build-prod   # to perform an optimised build for benchmarking
make test         # to run the tests
make testcov      # to run the tests and generate a coverage report
make lint         # to run the linter
make format       # to format python and rust code
make all          # to run to run build-dev + format + lint + test
```

### Useful Resources

* [`python/pydantic_core/_pydantic_core.pyi`](./python/pydantic_core/_pydantic_core.pyi) - Python API types
* [`python/pydantic_core/core_schema.py`](./python/pydantic_core/core_schema.py) - Core schema definitions
* [`tests/`](./tests) - Comprehensive usage examples

## Profiling

It's possible to profile the code using the [`flamegraph` utility from `flamegraph-rs`](https://github.com/flamegraph-rs/flamegraph). (Tested on Linux.) You can install this with `cargo install flamegraph`.

Run `make build-profiling` to install a release build with debugging symbols included (needed for profiling).

Once that is built, you can profile pytest benchmarks with (e.g.):

```bash
flamegraph -- pytest tests/benchmarks/test_micro_benchmarks.py -k test_list_of_ints_core_py --benchmark-enable
```
The `flamegraph` command will produce an interactive SVG at `flamegraph.svg`.

## Releasing

1. Bump package version locally. Do not just edit `Cargo.toml` on Github, you need both `Cargo.toml` and `Cargo.lock` to be updated.
2. Make a PR for the version bump and merge it.
3. Go to https://github.com/pydantic/pydantic-core/releases and click "Draft a new release"
4. In the "Choose a tag" dropdown enter the new tag `v<the.new.version>` and select "Create new tag on publish" when the option appears.
5. Enter the release title in the form "v<the.new.version> <YYYY-MM-DD>"
6. Click Generate release notes button
7. Click Publish release
8. Go to https://github.com/pydantic/pydantic-core/actions and ensure that all build for release are done successfully.
9. Go to https://pypi.org/project/pydantic-core/ and ensure that the latest release is published.
10. Done 🎉
