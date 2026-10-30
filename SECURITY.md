# Security Policy

If you think you have identified a security issue with Pydantic, **do not open a public issue**.

To responsibly report a security issue, please navigate to the "Security" tab of the repository, and click
["Report a vulnerability"](https://github.com/pydantic/pydantic/security/advisories/new).

Be sure to include clear details in your report:

* The affected version(s).
* A [MRE](https://en.wikipedia.org/wiki/Minimal_reproducible_example) of the issue. If possible, avoid complex setups
  (e.g. multiple files, repositories to clone, Docker setups). The MRE should make the issue obvious at a glance,
  without requiring maintainers to break it down to understand what is going on.
* The section of the [threat model](#threat-model) the issue falls under. If it doesn't fit any of them,
  explain why it should still be considered a security issue.
* Usage of AI tools to find or write up the issue is accepted. However, by submitting the report, you attest that you
  have reviewed and verified its content yourself. Repeated nonsensical reports may result in a ban from the
  Pydantic GitHub organization.

## Supported versions

Security fixes are only made to the latest minor release of Pydantic V2, and are published as a new patch release.
Fixes are not backported to older minor releases. Reports must be reproducible on the latest release.

Maintainers may still publish advisories for issues affecting older releases, depending on the severity.

## Threat model

This section describes the security boundaries and assumptions of Pydantic. Its goal is to be transparent about which
guarantees Pydantic provides, and which threats applications using Pydantic are expected to defend against themselves.
It is not a threat model for applications built with Pydantic.

### Overview

Pydantic is a data validation library. Its main components are:

* **Validation**: converting input data to Python objects conforming to a schema, derived from type hints
  (models, dataclasses, typed dictionaries, `TypeAdapter`). The input can either be Python data
  (`model_validate()`, `validate_python()`) or JSON data (`model_validate_json()`, `validate_json()`).
* **Serialization**: converting Python objects to Python primitives or JSON (`model_dump()`, `model_dump_json()`).
* **JSON Schema generation**.
* **pydantic-core**: the Rust implementation of validation and serialization, exposed to Python using PyO3.
  The `pydantic` package builds a [*core schema*](https://pydantic.dev/docs/validation/latest/internals/architecture/) from type hints,
  which pydantic-core uses to build a validator and a serializer. JSON data is parsed directly by pydantic-core, using the
  [jiter](https://github.com/pydantic/jiter) library.

### Trust boundaries

* **Untrusted**: the data being validated, when it is [user-controlled](#user-controlled-input).
* **Trusted**: everything defined by the application: type hints and schemas, configuration, custom validators
  and serializers, custom types, and the objects created by the application.

### Scope

Only issues related to the validation of user-controlled input, using the public API of [supported Pydantic versions](#supported-versions),
are considered as potential security issues. The following are out of scope:

* [Serialization](https://pydantic.dev/docs/validation/latest/concepts/serialization/) and [JSON Schema generation](https://pydantic.dev/docs/validation/latest/concepts/json_schema/),
  as they operate on data and schemas defined by the application.
* Schemas, configuration or type hints built from untrusted data (for instance, dynamically creating models with
  [`create_model()`](https://pydantic.dev/docs/validation/latest/concepts/models/#dynamic-model-creation) or providing
  a `pattern` constraint from user input).
* Behavior of code provided by the application (custom validators and serializers,
  `__get_pydantic_core_schema__()` implementations, etc).
* The [`@validate_call`](https://pydantic.dev/docs/validation/latest/concepts/validation_decorator/) decorator: it validates arguments passed by the application to its own functions.
* Private or undocumented APIs.

The exception is memory safety: an issue in `pydantic-core` (e.g. unsound `unsafe` code or misuse of PyO3) leading to
memory corruption, such as out-of-bounds reads or writes or use-after-free, is in scope regardless of the component
or the input involved.

#### User-controlled input

User-controlled input is data that can be provided directly by an external user, expected to be untrusted and
correctly validated by Pydantic:

* Every JSON input is considered user-controlled.
* Python input is considered user-controlled only when made of "native" data types: `dict`, `list`, `tuple`, `str`,
  `bytes`, `int`, `float`, `bool` and `None`. For example, such input can be obtained by first parsing JSON data
  using the standard library `json` module.

Instances of other types (such as `Decimal`, `Fraction`, `datetime`, model instances or custom classes) are not
user-controlled, as they are created by the application. If the application converts untrusted data to such types
before validation, it is responsible for this conversion.

For example, managing to crash the interpreter when validating an instance of a crafted type such as:

```python
class EvilList:
    def __iter__(self):
        return self

    def __next__(self):
        # Do stuff that crashes the interpreter
        ...
```

is *not* considered a security issue (unless it results in memory corruption, as described above).

### Security assumptions

Pydantic's security posture relies on the following assumptions. Applications are responsible for:

* **Bounding the size of user-controlled input** (e.g. using request body size limits of the web server, or
  `max_length` constraints). Pydantic is used in very different contexts (web APIs, configuration, data pipelines, etc)
  and thus cannot define a reasonable maximum input size.
* **Defining reasonable schemas**: schemas should plausibly exist in a production application and follow
  documented best practices.
* **Not relying on serialization to protect sensitive data**: fields excluded by the declared type (e.g. fields only
  present on a subclass), or with `include`/`exclude` filters, should not be the only control preventing sensitive
  data from being exposed. Use dedicated response models, `Field(exclude=True)` or secret types instead.
* **Not exposing validation errors containing sensitive data**: validation errors include the invalid input by default
  (this can be disabled using the [`hide_input_in_errors`](https://pydantic.dev/docs/validation/latest/api/pydantic/config/#pydantic.config.ConfigDict.hide_input_in_errors)
  configuration value).

### Threats

#### Validation bypass

Pydantic accepts user-controlled input that should be rejected according to the schema and the documented behavior.
[Coercions](https://pydantic.dev/docs/validation/latest/concepts/models/#data-conversion) (in lax mode) are not validation bypasses.
The following are examples of valid vulnerabilities:

* Accepting `'not_an_int'` for `int` types (`'1'` for `int` is fine due to type coercion).
* Allowing a list of length 3 for `Annotated[list, Field(max_length=2)]`.

#### Denial of service

Given that applications are expected to bound the size of user-controlled input, we only consider as a denial of
service a validation time or memory usage that grows **super-linearly** (quadratic or worse) with the size of the input,
and that is significant in practice: the resource usage should be disproportionate to the size of the input (e.g.
seconds of CPU time or hundreds of megabytes of memory for an input that would commonly be accepted).

##### 1. Super-linear growth (in scope)

The following would be considered a security issue:

```python
from pydantic import TypeAdapter

ta = TypeAdapter(int)

# If this were to take ~12s, as the validation time would grow with the value
# of the exponent (i.e. exponentially with the length of the input):
ta.validate_python('10e11212')
```

##### 2. Linear growth (out of scope)

Validation cost that grows linearly is expected, even with a large constant factor (it may still be reported as
a regular performance issue):

```python
from pydantic import TypeAdapter

ta = TypeAdapter(list[int])

# ~4MB of JSON data, using ~280MB of memory to hold one million validation errors.
# Memory grows linearly with the number of invalid items:
ta.validate_json('[' + ','.join(['"a"'] * 1_000_000) + ']')
```

##### 3. Schemas not following best practices (out of scope)

Super-linear behavior inherent to the documented semantics of a schema that doesn't follow best practices is not
considered a security issue. For example, with recursive models using untagged unions where every member can validate
the same nested data, the nested data is validated once per union member at each level, which is how untagged
unions work:

```python
from __future__ import annotations

from pydantic import BaseModel


class A(BaseModel):
    child: A | B | None


class B(BaseModel):
    child: A | B | None
```

[Discriminated unions](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions) should be used instead.

##### 4. Cost inherent to the produced object (out of scope)

Super-linear behavior inherent to the Python object being produced is not considered a security issue, as any code
producing the same object would be affected. For example, building a `dict` or `set` from crafted integers can be
quadratic, as integer hashes are not randomized in CPython. If this is a concern, the number of items can be bounded
using `max_length`:

```python
from typing import Annotated

from pydantic import Field, TypeAdapter

ta = TypeAdapter(Annotated[set[int], Field(max_length=100)])
```

Super-linear behavior introduced by Pydantic itself (i.e. not inherent to the object being produced) is still in scope.
