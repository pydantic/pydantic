[![BuildStatus](https://travis-ci.org/samuelcolvin/pydantic.svg?branch=master)](https://travis-ci.org/samuelcolvin/pydantic)
[![Coverage](https://codecov.io/gh/samuelcolvin/pydantic/branch/master/graph/badge.svg)](https://codecov.io/gh/samuelcolvin/pydantic)
[![pypi](https://img.shields.io/pypi/v/pydantic.svg)](https://pypi.python.org/pypi/pydantic)
[![CondaForge](https://img.shields.io/conda/v/conda-forge/pydantic.svg)](https://anaconda.org/conda-forge/pydantic)
[![downloads](https://img.shields.io/pypi/dm/pydantic.svg)](https://pypistats.org/packages/pydantic)
[![license](https://img.shields.io/github/license/samuelcolvin/pydantic.svg)](https://github.com/samuelcolvin/pydantic/blob/master/LICENSE)

{!.version.md!}

Data validation and settings management using python type annotations.

*pydantic* enforces type hints at runtime, and provides user friendly errors when data is invalid.

Define how data should be in pure, canonical python; validate it with *pydantic*.

!!! note "Version 0.32 Documentation"
    This documentation refers to Version 1 of *pydantic* which has just been released, **v0.32.2** 
    (the previous release) docs are available [here](https://5d584fcca7c9b70007d1c997--pydantic-docs.netlify.com).

## Example

```py
{!.tmp_examples/index_main.py!}
```
_(This script is complete, it should run "as is")_

What's going on here:

* `id` is of type int; the annotation-only declaration tells *pydantic* that this field is required. Strings,
  bytes or floats will be coerced to ints if possible; otherwise an exception will be raised.
* `name` is inferred as a string from the provided default; because it has a default, it is not required.
* `signup_ts` is a datetime field which is not required (and takes the value ``None`` if it's not supplied).
  *pydantic* will process either a unix timestamp int (e.g. `1496498400`) or a string representing the date & time.
* `friends` uses python's typing system, and requires a list of inputs. As with `id`, integer-like objects
  will be converted to integers.

If validation fails pydantic will raise an error with a breakdown of what was wrong:

```py
{!.tmp_examples/index_error.py!}
```
outputs:
```json
{!.tmp_examples/index_error.json!}
```

## Rationale

So *pydantic* uses some cool new language features, but why should I actually go and use it?

**plays nicely with your IDE/linter/brain**
: There's no new schema definition micro-language to learn. If you know how to use python type hints, 
  you know how to use *pydantic*. Data structures are just instances of classes you define with type annotations, 
  so auto-completion, linting, [mypy](usage/mypy.md), IDEs (especially [PyCharm](pycharm_plugin.md)), 
  and your intuition should all work properly with your validated data.

**dual use**
: *pydantic's* [BaseSettings](usage/settings.md) class allows *pydantic* to be used in both a "validate this request
  data" context and in a "load my system settings" context. The main differences are that system settings can
  be read from environment variables, and more complex objects like DSNs and python objects are often required.

**fast**
: In [benchmarks](benchmarks.md) *pydantic* is faster than all other tested libraries.

**validate complex structures**
: use of [recursive *pydantic* models](usage/models.md#recursive-models), `typing`'s 
  [standard types](usage/types.md#standard-library-types) (e.g. `List`, `Tuple`, `Dict` etc.) and 
  [validators](usage/validators.md) allow
  complex data schemas to be clearly and easily defined, validated, and parsed.

**extensible**
: *pydantic* allows [custom data types](usage/types.md#custom-data-types) to be defined or you can extend validation 
  with methods on a model decorated with the [`validator`](usage/validators.md) decorator.
  
**dataclasses integration**
: As well as `BaseModel`, *pydantic* provides
  a [`dataclass`](usage/dataclasses.md) decorator which creates (almost) vanilla python dataclasses with input
  data parsing and validation.

## Using Pydantic

Hundreds of organisations and packages are using *pydantic*, including:

[FastAPI](https://fastapi.tiangolo.com/)
: a high performance API framework, easy to learn,
  fast to code and ready for production, based on *pydantic* and Starlette.

[Project Jupyter](https://jupyter.org/)
: developers of the Jupyter notebook are using *pydantic* 
  [for subprojects](https://github.com/samuelcolvin/pydantic/issues/773).

**Microsoft**
: are using *pydantic* (via FastAPI) for 
  [numerous services](https://github.com/tiangolo/fastapi/pull/26#issuecomment-463768795), some of which are 
  "getting integrated into the core Windows product and some Office products."

**Amazon Web Services**
: are using *pydantic* in [gluon-ts](https://github.com/awslabs/gluon-ts), an open-source probabilistic time series
  modeling library.

**The NSA**
: are using *pydantic* in [WALKOFF](https://github.com/nsacyber/WALKOFF), an open-source automation framework.

**Uber**
: are using *pydantic* in [Ludwig](https://github.com/uber/ludwig), an an open-source TensorFlow wrapper.

**Cuenca**
: are a Mexican neobank that uses *pydantic* for several internal
  tools (including API validation) and for open source projects like
  [stpmex](https://github.com/cuenca-mx/stpmex-python), which is used to process real-time, 24/7, inter-bank
  transfers in Mexico.

[The Molecular Sciences Software Institute](https://molssi.org)
: are using *pydantic* in [QCFractal](https://github.com/MolSSI/QCFractal), a massively distributed compute framework
  for quantum chemistry.

For a more comprehensive list of open-source projects using *pydantic* see the 
[list of dependents on github](https://github.com/samuelcolvin/pydantic/network/dependents).
