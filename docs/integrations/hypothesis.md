[Hypothesis](https://hypothesis.readthedocs.io/) is the Python library for
[property-based testing](https://increment.com/testing/in-praise-of-property-based-testing/).
Hypothesis can infer how to construct type-annotated classes, and supports builtin types,
many standard library types, and generic types from the
[`typing`](https://docs.python.org/3/library/typing.html) and
[`typing_extensions`](https://pypi.org/project/typing-extensions/) modules by default.

Pydantic v2.0 drops built-in support for Hypothesis and no more ships with the integrated Hypothesis plugin.

!!! warning
    We are temporarily removing the Hypothesis plugin in favor of studying a different mechanism. For more information, see the issue [annotated-types/annotated-types#37](https://github.com/annotated-types/annotated-types/issues/37).

    The Hypothesis plugin may be back in a future release. Subscribe to [pydantic/pydantic#4682](https://github.com/pydantic/pydantic/issues/4682) for updates.
