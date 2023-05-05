[Hypothesis](https://hypothesis.readthedocs.io/) is the Python library for
[property-based testing](https://increment.com/testing/in-praise-of-property-based-testing/).
Hypothesis can infer how to construct type-annotated classes, and supports builtin types,
many standard library types, and generic types from the
[`typing`](https://docs.python.org/3/library/typing.html) and
[`typing_extensions`](https://pypi.org/project/typing-extensions/) modules by default.

Pydantic v2.0 drops built-in support for Hypothesis and no more ships with the integrated Hypothesis plugin.

It is possible that Hypothesis plugin will be back as a separate library for Pydantic v2.0+ series (see [V2: hypothesis plugin rewrite · Issue #4682 · pydantic/pydantic](https://github.com/pydantic/pydantic/issues/4682)).
