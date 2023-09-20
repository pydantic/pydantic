Where possible Pydantic uses [standard library types](standard_types.md) to define fields, thus smoothing
the learning curve. For many useful applications, however, no standard library type exists,
so Pydantic implements many commonly used types.

There are also more complex types that can be found in the
[Pydantic Extra Types](https://github.com/pydantic/pydantic-extra-types) package.

If no existing type suits your purpose you can also implement your [own Pydantic-compatible types](custom.md#custom-data-types) with custom properties and validation.

The following sections describe the types supported by Pydantic.


* [Standard Library Types](standard_types.md) &mdash; types from the Python standard library.
* [Strict Types](strict_types.md) &mdash; types that enable you to prevent coercion from compatible types.
* [Types with Fields](types_fields.md) &mdash; types that allow you to define fields.
* [Custom Data Types](custom.md) &mdash; create your own custom data types.
* [Field Type Conversions](../conversion_table.md) &mdash; strict and lax conversion between different field types.
