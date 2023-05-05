[Hypothesis](https://hypothesis.readthedocs.io/) is the Python library for
[property-based testing](https://increment.com/testing/in-praise-of-property-based-testing/).
Hypothesis can infer how to construct type-annotated classes, and supports builtin types,
many standard library types, and generic types from the
[`typing`](https://docs.python.org/3/library/typing.html) and
[`typing_extensions`](https://pypi.org/project/typing-extensions/) modules by default.

Pydantic v2.0 drops built-in support for Hypothesis and no more ships with the integrated Hypothesis plugin.

We are temporarily removing the Hypothesis plugin in favor of another mechanism discussed here - [Way to communicate more information between libraries · Issue #37 · annotated-types/annotated-types](https://github.com/annotated-types/annotated-types/issues/37).
It is also possible that Hypothesis plugin will be back in Pydantic v2.0+ (see [V2: hypothesis plugin rewrite · Issue #4682 · pydantic/pydantic](https://github.com/pydantic/pydantic/issues/4682)).
