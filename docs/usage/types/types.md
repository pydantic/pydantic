Where possible Pydantic uses [standard library types](standard_types.md) to define fields, thus smoothing
the learning curve. For many useful applications, however, no standard library type exists,
so Pydantic implements many commonly used types.

There are also more complex types that can be found in the [Pydantic Extra Types](extra_types/extra_types.md).

If no existing type suits your purpose you can also implement your [own Pydantic-compatible types](custom.md#custom-data-types) with custom properties and validation.

The following sections describe the types supported by Pydantic.


* [Standard Library Types](standard_types.md) &mdash; types from the Python standard library.
* [Callables](callables.md) &mdash; `Callable` types.
* [Dicts and Mapping Types](dicts_mapping.md) &mdash; `dict` types and mapping types.
* [Enums and Choices](enums.md) &mdash; uses Python's standard `enum` classes to define choices.
* [JSON](json.md) &mdash; a type that allows you to store JSON data in your model.
* [Lists and Tuples](list_types.md) &mdash; `list` and `tuple` types.
* [Number Types](number_types.md) &mdash; `int`, `float`, `Decimal`, and other number types.
* [Sequence, Iterable, & Iterator](sequence_iterable.md) &mdash; iterable types including `Sequence`, `Iterable`, and `Iterator`.
* [Sets and frozenset](set_types.md) &mdash; `set` and `frozenset` types.
* [Strict Types](strict_types.md) &mdash; types that enable you to prevent coercion from compatible types.
* [Type and TypeVar](typevars.md) &mdash; `Type` and `TypeVar` types.
* [Types with Fields](types_fields.md) &mdash; types that allow you to define fields.
* [Unions](unions.md) &mdash; allows a model attribute to accept different types.
* [URLs](urls.md) &mdash; URI/URL validation types.
* [UUIDs](uuids.md) &mdash; types that allow you to store UUIDs in your model.
* [Custom Data Types](custom.md) &mdash; create your own custom data types.
* [Field Type Conversions](../conversion_table.md) &mdash; strict and lax conversion between different field types.
* [Extra Types](extra_types/extra_types.md): Types that can be found in the optional [Pydantic Extra Types](https://github.com/pydantic/pydantic-extra-types) package. These include:
    * [Color Types](extra_types/color_types.md) &mdash; types that enable you to store RGB color values in your model.
    * [Payment Card Numbers](extra_types/payment_cards.md) &mdash; types that enable you to store payment cards such as debit or credit cards.
    * [Phone Numbers](extra_types/phone_numbers.md) &mdash; types that enable you to store phone numbers in your model.
    * [Routing Numbers](extra_types/color_types.md) &mdash; types that enable you to store ABA routing transit numbers in your model.
