[Hypothesis](https://hypothesis.readthedocs.io/) is the Python library for
[property-based testing](https://increment.com/testing/in-praise-of-property-based-testing/).
Hypothesis can infer how to construct type-annotated classes, and supports builtin types,
many standard library types, and generic types from the
[`typing`](https://docs.python.org/3/library/typing.html) and
[`typing_extensions`](https://pypi.org/project/typing-extensions/) modules by default.

From Pydantic v1.8 and [Hypothesis v5.29.0](https://hypothesis.readthedocs.io/en/latest/changes.html#v5-29-0),
Hypothesis will automatically load support for [custom types](usage/types.md) like
`PaymentCardNumber` and `PositiveFloat`, so that the
[`st.builds()`](https://hypothesis.readthedocs.io/en/latest/data.html#hypothesis.strategies.builds)
and [`st.from_type()`](https://hypothesis.readthedocs.io/en/latest/data.html#hypothesis.strategies.from_type)
strategies support them without any user configuration.

!!! warning
    Please note, while the plugin supports these types, hypothesis will(currently) generate values outside 
    of given args for the constrained function types.


### Example tests

```py
{!.tmp_examples/hypothesis_property_based_test.py!}
```
_(This script is complete, it should run "as is")_


### Use with JSON Schemas

To test client-side code, you can use [`Model.schema()`](usage/models.md) with the
[`hypothesis-jsonschema` package](https://pypi.org/project/hypothesis-jsonschema/)
to generate arbitrary JSON instances matching the schema.
For web API testing, [Schemathesis](https://schemathesis.readthedocs.io) provides
a higher-level wrapper and can detect both errors and security vulnerabilities.
