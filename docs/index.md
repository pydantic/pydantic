<div>
  <a href="https://travis-ci.org/samuelcolvin/pydantic" target="_blank">
    <img src="https://travis-ci.org/samuelcolvin/pydantic.svg?branch=master" alt="Build Status">
  </a>
  <a href="https://codecov.io/gh/samuelcolvin/pydantic" target="_blank">
    <img src="https://codecov.io/gh/samuelcolvin/pydantic/branch/master/graph/badge.svg" alt="Coverage">
  </a>
  <a href="https://pypi.org/project/fastapi" target="_blank">
    <img src="https://badge.fury.io/py/fastapi.svg" alt="Package version">
  </a>
  <a href="https://anaconda.org/conda-forge/pydantic" target="_blank">
    <img src="https://img.shields.io/conda/v/conda-forge/pydantic.svg" alt="CondaForge">
  </a>
  <a href="https://pypistats.org/packages/pydantic" target="_blank">
    <img src="https://img.shields.io/pypi/dm/pydantic.svg" alt="downloads">
  </a>
  <a href="https://github.com/samuelcolvin/pydantic" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/pydantic.svg" alt="versions">
  </a>
  <a href="https://github.com/samuelcolvin/pydantic/blob/master/LICENSE" target="_blank">
    <img src="https://img.shields.io/github/license/samuelcolvin/pydantic.svg" alt="license">
  </a>
</div>

!!! note
    These docs refer to Version 1 of *pydantic* which is as-yet unreleased, *v0.32* docs are available
    [here](https://5d5d36c5b8219300085d081b--pydantic-docs.netlify.com).

Data validation and settings management using python type hinting.

Define how data should be in pure, canonical python; validate it with *pydantic*.

[PEP 484](https://www.python.org/dev/peps/pep-0484/) introduced type hinting into python 3.5,
[PEP 526](https://www.python.org/dev/peps/pep-0526/) extended that with syntax for variable annotation in python 3.6.

*pydantic* uses those annotations to validate that untrusted data takes the form you want.

There's also support for an extension to [dataclasses](https://docs.python.org/3/library/dataclasses.html)
where the input data is validated.

Example:

```py
{!./examples/example1.py!}
```

(This script is complete, it should run "as is")

What's going on here:

* `id` is of type int; the annotation only declaration tells *pydantic* that this field is required. Strings,
  bytes or floats will be coerced to ints if possible, otherwise an exception would be raised.
* `name` is inferred as a string from the default, it is not required as it has a default.
* `signup_ts` is a datetime field which is not required (``None`` if it's not supplied), pydantic will process
  either a unix timestamp int (e.g. `1496498400`) or a string representing the date & time.
* `friends` uses python's typing system, it is required to be a list of integers, as with `id` integer-like objects
  will be converted to integers.

If validation fails pydantic with raise an error with a breakdown of what was wrong:

```py
{!./examples/example2.py!}
```

## Rationale


So *pydantic* uses some cool new language feature, but why should I actually go and use it?

**no brainfuck**
    no new schema definition micro-language to learn. If you know python (and perhaps skim read the
    [type hinting docs](https://docs.python.org/3/library/typing.html)) you know how to use *pydantic*.

**plays nicely with your IDE/linter/brain**
    because *pydantic* data structures are just instances of classes you define; auto-completion, linting,
    [mypy](usage.md#usage_mypy), IDEs (especially [PyCharm](pycharm_plugin.md)) and your intuition should all work properly with your validated data.

**dual use**
    *pydantic's* [BaseSettings](usage.md#settings) class allows it to be used in both a "validate this request data"
    context and "load my system settings" context. The main difference being that system settings can have defaults
    changed by environment variables and more complex objects like DSNs and python objects are often required.

**fast**
    In [benchmarks](benchmarks.md) *pydantic* is faster than all other tested libraries.

**validate complex structures**
    use of recursive *pydantic* models, `typing`'s `List` and `Dict` etc. and validators allow
    complex data schemas to be clearly and easily defined and then checked.

**extensible**
    *pydantic* allows custom data types to be defined or you can extend validation with methods on a model decorated
    with the `validator` decorator.
